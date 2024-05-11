import asyncio
import logging

import prisma
import prisma.enums
import pydantic
from langsmith import traceable
from prisma.models import Application

import codex.common.model
import codex.common.types
import codex.interview.ai_module
import codex.interview.database
import codex.interview.model
import codex.requirements.blocks.ai_database
import codex.requirements.blocks.ai_endpoint
import codex.requirements.blocks.ai_module_routes
import codex.requirements.model
from codex.api_model import Identifiers
from codex.common.model import APIRouteSpec

logger = logging.getLogger(__name__)


class Module(pydantic.BaseModel):
    """
    A Software Module for the application
    """

    name: str
    description: str
    interactions: str
    api_routes: list[APIRouteSpec]


class SpecHolder(pydantic.BaseModel):
    """
    A Software Module for the application
    """

    ids: Identifiers
    app: Application
    features: list[prisma.models.Feature] = []
    modules: list[Module] = []
    db_response: codex.requirements.model.DBResponse | None = None


@traceable
async def generate_requirements(ids: Identifiers, app: Application) -> SpecHolder:
    """
    Runs the Requirements Agent to generate the system requirements based
    upon the provided task

    The new V2 version of the requirements agent uses a simplifed flow:

    1. Get the last interview step
    2. Generate the modules
    3. Generate the database design
    4. [Parrallelized] For each module, generate the API Routes it needs
    5. [Parrallelized] For each API Route, generate the detailed API Spec

    In future there will be a simple and advanced mode for generating the requirements

    The simple mode will only allow the user to interact at the interview level
    The advanced mode will allow the user to interact at the module and API level

    Args:
        ids (Identifiers): Relevant ids for database operations
        description (str): description of the application

    Returns:
        ApplicationRequirements: The system requirements for the application
    """
    if not ids.user_id or not ids.app_id:
        raise ValueError("User and App Ids are required")

    spec_holder = SpecHolder(
        ids=ids,
        app=app,
    )

    logger.info("Spec Definition Started")
    if not ids.interview_id:
        raise ValueError("Interview ID is required")

    # User Interview
    interview = await codex.interview.database.get_last_interview_step(
        interview_id=ids.interview_id, app_id=ids.app_id
    )

    if not interview or not interview.Features:
        raise ValueError("Interview not found or no features defined")
    if not interview.Modules:
        raise ValueError("No Modules defined")
    if interview.access_roles:
        access_roles = ", ".join(a for a in interview.access_roles)
    else:
        access_roles = ""

    spec_holder.features = interview.Features

    features_string = ""
    for feature in interview.Features:
        features_string += "\nFeature Name: " + str(feature.name)
        features_string += "\nFunctionality: " + str(feature.functionality)
        features_string += "\nReasoning: " + str(feature.reasoning)
        features_string += "\n"

    logger.info("Defining Modules from features")

    modules_string = ""
    for module in interview.Modules:
        modules_string += "\nModule Name: " + str(module.name)
        modules_string += "\nFunctionality: " + str(module.description)
        modules_string += "\n"

    logger.info("Designing Database")
    # Database Design
    database_block = codex.requirements.blocks.ai_database.DatabaseGenerationBlock()

    product_spec_str = f"{app.name} - {app.description}\nFeatures:\n{features_string}"

    db_invoke_params = {
        "product_spec": product_spec_str,
        "needed_auth_roles": access_roles,
        "modules": modules_string,
    }

    db_response: codex.requirements.model.DBResponse = await database_block.invoke(
        ids=ids,
        invoke_params=db_invoke_params,
    )

    spec_holder.db_response = db_response

    logger.info("Specifying Module API Routes")

    modules = await asyncio.gather(
        *[
            denfine_module_routes(
                ids=ids,
                app=app,
                module_reqs=m,
                roles=access_roles,
                db_response=db_response,
            )
            for m in interview.Modules
        ]
    )

    spec_holder.modules = modules

    logger.info("Specification Definition Complete, saving to database")
    return spec_holder


@traceable
async def denfine_module_routes(
    ids: Identifiers,
    app: Application,
    module_reqs: prisma.models.Module,
    roles: str,
    db_response: codex.requirements.model.DBResponse,
) -> Module:
    logger.warning(
        f"Defining API Routes for Module: {module_reqs.name} - {module_reqs.description}"
    )

    block = codex.requirements.blocks.ai_module_routes.ModuleGenerationBlock()

    module_routes = await block.invoke(
        ids=ids,
        invoke_params={
            "poduct_name": app.name,
            "product_description": app.description,
            "module": f"{module_reqs.name} - {module_reqs.description}",
            "interactions": module_reqs.interactions,
            "roles": roles,
        },
    )
    for r in module_routes.routes:
        logger.warning(f"Route: {r.http_verb} - {r.path} - {r.description}")

    endpoints = await asyncio.gather(
        *[
            define_api_spec(
                ids=ids,
                app=app,
                module_reqs=module_reqs,
                api_route=route,
                db_response=db_response,
            )
            for route in module_routes.routes
        ]
    )

    module = Module(
        name=module_reqs.name,
        description=module_reqs.description,
        interactions=module_reqs.interactions,
        api_routes=endpoints,
    )

    return module


@traceable
async def define_api_spec(
    ids: Identifiers,
    app: Application,
    module_reqs: prisma.models.Module,
    api_route: codex.requirements.blocks.ai_module_routes.APIRoute,
    db_response: codex.requirements.model.DBResponse,
):
    block = codex.requirements.blocks.ai_endpoint.EndpointSchemaRefinementBlock()
    model_names = [table.name for table in db_response.database_schema.tables]

    enum_names = [enum.name for enum in db_response.database_schema.enums]

    allowed_types = (
        model_names + enum_names + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    endpoint: codex.requirements.model.EndpointSchemaRefinementResponse = await block.invoke(
        ids=ids,
        invoke_params={
            "spec": f"{app.name} - {app.description}",
            "db_models": db_response.database_schema.tables,
            "db_enums": db_response.database_schema.enums,
            "module_repr": f"{module_reqs.name} - {module_reqs.description}",
            "endpoint_repr": f"{api_route.http_verb} - {api_route.path} - {api_route.description} \n Roles Allowed: {', '.join(api_route.allowed_access_roles)}",
            "allowed_types": allowed_types,
        },
    )

    assert endpoint.api_endpoint.request_model is not None, "Request Model is None"
    assert endpoint.api_endpoint.response_model is not None, "Response Model is None"
    assert (
        endpoint.api_endpoint.request_model.Fields is not None
    ), "Request Model Fields is None"
    assert (
        endpoint.api_endpoint.response_model.Fields is not None
    ), "Response Model Fields is None"

    api_spec = APIRouteSpec(
        module_name=module_reqs.name,
        access_level=api_route.access_level,
        http_verb=api_route.http_verb,
        function_name=api_route.function_name,
        path=api_route.path,
        description=api_route.description,
        allowed_access_roles=api_route.allowed_access_roles,
        request_model=endpoint.api_endpoint.request_model,
        response_model=endpoint.api_endpoint.response_model,
    )

    return api_spec
