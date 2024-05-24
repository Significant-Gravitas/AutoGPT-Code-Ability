import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

import codex.database
import codex.develop.agent as architect_agent
import codex.develop.database
import codex.requirements.blocks.ai_endpoint
import codex.requirements.database
from codex.api_model import (
    ApplicationCreate,
    DeliverableResponse,
    DeliverablesListResponse,
    FunctionRequest,
    Identifiers,
)
from codex.common.model import FunctionSpec
from codex.develop.model import FunctionResponse

logger = logging.getLogger(__name__)

delivery_router = APIRouter()


# Deliverables endpoints
@delivery_router.post(
    "/function/",
    tags=["function"],
)
async def write_function(func_req: FunctionRequest) -> FunctionResponse:
    """
    Writes a function based on the provided FunctionRequest.

    Args:
        func_req (FunctionRequest): The FunctionRequest object containing the details of the function.

    Returns:
        FunctionResponse: The FunctionResponse object containing the ID, name, requirements, and code of the completed function.
    """

    user = await codex.database.get_or_create_user_by_cloud_services_id_and_discord_id(
        "AutoGPT", "AutoGPT"
    )
    # Create App for this function
    app = await codex.database.create_app_db(
        user.id,
        ApplicationCreate(name=func_req.name, description=func_req.description),
    )

    ids = Identifiers(user_id=user.id, app_id=app.id)
    try:
        ai_block = codex.requirements.blocks.ai_endpoint.EndpointSchemaRefinementBlock()
        endpoint_resp = await ai_block.invoke(
            ids=Identifiers(user_id=user.id, app_id=app.id),
            invoke_params={
                "spec": f"{func_req.name} - {func_req.description}",
                "endpoint_repr": f"{func_req.name} - {func_req.description}\n Inputs: {func_req.inputs}\n Outputs: {func_req.outputs}",
                "allowed_types": codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES,
            },
        )
        endpoint = endpoint_resp.api_endpoint
        function_spec = FunctionSpec(
            name=func_req.name,
            description=func_req.description,
            func_args=endpoint.request_model,
            return_type=endpoint.response_model,
        )
    except Exception as e:
        logger.error(f"Error creating function spec: {e}")
        raise RuntimeError("Error creating function spec")

    completed_function: codex.database.CompiledRoute = (
        await architect_agent.write_function(ids, app, function_spec)
    )
    package_requirements = []
    if completed_function.Packages:
        for package in completed_function.Packages:
            package_requirements.append(
                f"{package.packageName}{f':^{package.version}' if package.version else '=*'}"
            )

    return FunctionResponse(
        id=completed_function.id,
        name=completed_function.mainFunctionName,
        requirements=package_requirements,
        code=completed_function.compiledCode,
    )


@delivery_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    tags=["deliverables"],
    response_model=DeliverableResponse,
)
async def create_deliverable(user_id: str, app_id: str, spec_id: str):
    """
    Create a new deliverable (completed app) for a specific specification.
    """
    specification = await codex.requirements.database.get_specification(
        user_id, app_id, spec_id
    )
    user = await codex.database.get_user(user_id)
    app = await codex.database.get_app_by_id(user_id, app_id)
    logger.info(f"Creating deliverable for {app.name}")
    if specification:
        ids = Identifiers(
            user_id=user_id,
            cloud_services_id=user.cloudServicesId if user else "",
            app_id=app_id,
            spec_id=spec_id,
        )
        # Architect agent creates the code graphs for the requirements
        completed_app = await architect_agent.develop_application(ids, specification)

        return DeliverableResponse(
            id=completed_app.id,
            created_at=completed_app.createdAt,
            name=completed_app.name,
            description=completed_app.description,
        )
    else:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
            media_type="application/json",
        )


# Deliverables endpoints
@delivery_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/route/",
    tags=["deliverables"],
    response_model=DeliverableResponse,
)
async def create_single_deliverable_route(
    user_id: str, app_id: str, spec_id: str, api_route_spec_id: str
):
    """
    Create a new deliverable (completed app) for a specific specification.
    """
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
    )
    specification = await codex.requirements.database.get_specification(
        user_id, app_id, spec_id
    )
    user = await codex.database.get_user(user_id)
    app = await codex.database.get_app_by_id(user_id, app_id)
    api_route = await codex.database.get_api_route_by_id(
        ids=ids, api_route_id=api_route_spec_id
    )
    logger.info(f"Creating route deliverable for {app.name}")
    if specification:
        ids = Identifiers(
            user_id=user_id,
            cloud_services_id=user.cloudServicesId if user else "",
            app_id=app_id,
            spec_id=spec_id,
        )
        # Check the route_id exists in the specification

        completed_app = await codex.database.create_completed_app(ids, specification)

        # If the completed app is defined, use the functions from the provided completed app as already implemented functions.
        # This flow is used for developing the user interface.
        if ids.completed_app_id:
            existing_completed_app = await codex.develop.database.get_deliverable(
                deliverable_id=ids.completed_app_id,
            )
            extra_functions = [
                route.RootFunction
                for route in existing_completed_app.CompiledRoutes or []
                if route.RootFunction
            ]

        else:
            extra_functions = []

        await architect_agent.process_api_route(
            api_route, ids, specification, completed_app, extra_functions
        )

        # TODO: Do somethig with the compiled route

        return DeliverableResponse(
            id=completed_app.id,
            created_at=completed_app.createdAt,
            name=completed_app.name,
            description=completed_app.description,
        )
    else:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
            media_type="application/json",
        )


@delivery_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    tags=["deliverables"],
)
async def create_user_interface(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str
):
    """
    Create a user interface from the existing back-end deliverable.
    """
    ids = Identifiers(user_id=user_id, app_id=app_id, spec_id=spec_id)
    user_interface = await architect_agent.develop_user_interface(ids)
    return DeliverableResponse(
        id=user_interface.id,
        created_at=user_interface.createdAt,
        name=user_interface.name,
        description=user_interface.description,
    )


@delivery_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    tags=["deliverables"],
)
async def get_deliverable(user_id: str, app_id: str, spec_id: str, deliverable_id: str):
    """
    Retrieve a specific deliverable (completed app) including its compiled routes by ID.
    """
    deliverable = await codex.develop.database.get_deliverable(deliverable_id)
    return DeliverableResponse(
        id=deliverable.id,
        created_at=deliverable.createdAt,
        name=deliverable.name,
        description=deliverable.description,
    )


@delivery_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    tags=["deliverables"],
)
async def delete_deliverable(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str
):
    """
    Delete a specific deliverable (completed app) by ID.
    """
    await codex.develop.database.delete_deliverable(
        user_id, app_id, spec_id, deliverable_id
    )
    return JSONResponse(
        content={"message": "Deliverable deleted successfully"},
        status_code=200,
    )


@delivery_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    response_model=DeliverablesListResponse,
    tags=["deliverables"],
)
async def list_deliverables(
    user_id: str,
    app_id: str,
    spec_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all deliverables (completed apps) for a specific specification."""
    deliverables, pagination = await codex.develop.database.list_deliverables(
        user_id, app_id, spec_id, page, page_size
    )

    return DeliverablesListResponse(
        deliverables=[
            DeliverableResponse(
                id=d.id,
                created_at=d.createdAt,
                name=d.name,
                description=d.description,
            )
            for d in deliverables
        ],
        pagination=pagination,
    )
