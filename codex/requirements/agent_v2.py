import asyncio
import logging

import pydantic
from prisma.models import Application, Specification

import codex.common.types
import codex.interview.database
import codex.requirements.blocks.ai_database
import codex.requirements.blocks.ai_endpoint_v2
import codex.requirements.blocks.ai_module_routes
import codex.requirements.blocks.ai_module_v2
import codex.requirements.model
from codex.api_model import Identifiers

logger = logging.getLogger(__name__)


async def generate_requirements(ids: Identifiers, app: Application) -> Specification:
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

    logger.info("State Object Created")

    # User Interview
    interview = await codex.interview.database.get_last_interview_step(
        interview_id=ids.interview_id, app_id=ids.app_id
    )

    features_string = ""
    for feature in interview.features:
        features_string += "\nFeature Name: " + str(feature.name)
        features_string += "\nFunctionality: " + str(feature.functionality)
        features_string += "\nReasoning: " + str(feature.reasoning)
        features_string += "\n"

    module_block = codex.requirements.blocks.ai_module_v2.ModuleGenerationBlock()
    module_response = await module_block.invoke(
        ids=ids,
        invoke_params={
            "poduct_name": app.name,
            "product_description": app.description,
            "features": interview.features,
        },
    )

    logger.info("DB Started")
    # Database Design
    database_block = codex.requirements.blocks.ai_database.DatabaseGenerationBlock()

    product_spec_str = f"{app.name} - {app.description}\nFeatures:\n{features_string}"

    db_invoke_params = {
        "product_spec": product_spec_str,
        "needed_auth_roles": ", ".join(a for a in module_response.access_level),
        "modules": ", ".join(module.name for module in module_response.modules),
    }

    db_response: codex.requirements.model.DBResponse = await database_block.invoke(
        ids=ids,
        invoke_params=db_invoke_params,
    )

    logger.info(f"DB Finished {db_response}")

    module_routes = await asyncio.gather(
        *[
            denfine_module_routes(
                ids=ids,
                app=app,
                module=module,
                features=features_string,
                roles=", ".join(module_response.access_roles),
                db_response=db_response,
            )
            for module in module_response.modules
        ]
    )

    api_routes = [route for module in module_routes for route in module]

    return api_routes


async def denfine_module_routes(
    ids: Identifiers,
    app: Application,
    module_reqs: codex.requirements.blocks.ai_module_v2.Module,
    features: str,
    roles: str,
    db_response: codex.requirements.model.DBResponse,
) -> list[codex.requirements.blocks.ai_module_routes.APIRoute]:
    block = codex.requirements.blocks.ai_module_routes.ModuleGenerationBlock()

    module_routes = await block.invoke(
        ids=ids,
        invoke_params={
            "poduct_name": app.name,
            "product_description": app.description,
            "features": features,
            "module": f"{module_reqs.name} - {module_reqs.description}",
            "roles": roles,
        },
    )

    endpoints = await asyncio.gather(
        *[
            define_api_spec(
                ids=ids,
                app=app,
                features=features,
                module=module_reqs,
                api_route=route,
                db_response=db_response,
            )
            for route in module_routes.modules
        ]
    )

    return endpoints


class APIRouteSpec(pydantic.BaseModel):
    """
    A Software Module for the application
    """

    module_name: str
    http_verb: str
    path: str
    description: str
    allowed_access_roles: list[str]
    request_model: codex.common.types.ObjectTypeE
    response_model: codex.common.types.ObjectTypeE


async def define_api_spec(
    ids: Identifiers,
    app: Application,
    features: str,
    module_reqs: codex.requirements.blocks.ai_module_v2.Module,
    api_route: codex.requirements.blocks.ai_module_routes.APIRoute,
    db_response: codex.requirements.model.DBResponse,
):
    block = codex.requirements.blocks.ai_endpoint_v2.EndpointGenerationBlock()

    endpoint: codex.requirements.model.EndpointSchemaRefinementResponse = await block.invoke(
        ids=ids,
        invoke_params={
            "spec": f"{app.name} - {app.description}\nFeatures:\n{features}",
            "db_models": db_response.models,
            "db_enums": db_response.enums,
            "module_repr": f"{module_reqs.name} - {module_reqs.description}",
            "endpoint_repr": f"{api_route.http_verb} - {api_route.path} - {api_route.description} \n Roles Allowed: {', '.join(api_route.allowed_access_roles)}",
        },
    )

    api_spec = APIRouteSpec(
        module_name=module_reqs.name,
        http_verb=api_route.http_verb,
        path=api_route.path,
        description=api_route.description,
        allowed_access_roles=api_route.allowed_access_roles,
        request_model=endpoint.api_endpoint.request_model,
        response_model=endpoint.api_endpoint.response_model,
    )

    return api_spec
