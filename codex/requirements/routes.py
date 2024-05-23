import logging
import pprint
from typing import Literal

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

import codex.database
import codex.requirements.agent
import codex.requirements.blocks.ai_endpoint
import codex.requirements.database
from codex.api_model import (
    Identifiers,
    ObjectFieldModel,
    SpecificationAddRouteToModule,
    SpecificationResponse,
    SpecificationsListResponse,
)

logger = logging.getLogger(__name__)

spec_router = APIRouter()


# Specs endpoints
@spec_router.post(
    "/user/{user_id}/apps/{app_id}/specs/",
    tags=["specs"],
    response_model=SpecificationResponse,
)
async def create_spec(
    user_id: str,
    app_id: str,
    interview_id: str,
) -> Response | SpecificationResponse:
    """
    Create a new specification for a given application and user.
    """
    await codex.database.get_app_response_by_id(user_id, app_id)
    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        interview_id=interview_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )
    if not ids.user_id or not ids.app_id:
        raise ValueError("User ID and App ID are required")

    app = await codex.database.get_app_by_id(user_id, app_id)
    if not app.description:
        raise ValueError("Application description is required")

    spec_holder = await codex.requirements.agent.generate_requirements(ids, app=app)
    new_spec = await codex.requirements.database.create_specification(spec_holder)

    spec_response = SpecificationResponse.from_specification(new_spec)
    spec_response.name = app.name
    spec_response.context = app.description or ""
    return spec_response


@spec_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}",
    response_model=SpecificationResponse,
    tags=["specs"],
)
async def get_spec(user_id: str, app_id: str, spec_id: str):
    """
    Retrieve a specific specification by its ID for a given application and user.
    """
    specification = await codex.requirements.database.get_specification(
        user_id, app_id, spec_id
    )
    if specification:
        return SpecificationResponse.from_specification(specification)
    else:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )


@spec_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/modules",
    tags=["specs"],
)
async def add_module(
    user_id: str,
    app_id: str,
    spec_id: str,
    module_name: str,
    description: str,
    interactions: str,
):
    """
    Add a new module to a specific specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    # Add the module to the spec
    module = await codex.requirements.database.add_module_to_specification(
        spec_id=spec.id,
        module_name=module_name,
        module_description=description,
        module_interactions=interactions,
    )

    return JSONResponse(
        content={"message": "Module added successfully", "module_id": module.id},
        status_code=200,
    )


@spec_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/modules/{module_id}",
    tags=["specs"],
)
async def delete_module(
    user_id: str,
    app_id: str,
    spec_id: str,
    module_id: str,
):
    """
    Delete a specific module by its ID from a specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    # Delete the module from the spec
    await codex.requirements.database.delete_module_from_specification(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        module_id=module_id,
    )

    return JSONResponse(
        content={"message": "Module deleted successfully"},
        status_code=200,
    )


@spec_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/modules/{module_id}/routes",
    tags=["specs"],
)
async def add_route(
    user_id: str,
    app_id: str,
    spec_id: str,
    module_id: str,
    route: SpecificationAddRouteToModule,
):
    """
    Add a new route to a specific specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    logger.info(pprint.pformat(route))

    # Add the route to the spec
    added_route = await codex.requirements.database.add_route_to_module(
        module_id, route
    )

    return JSONResponse(
        content={"message": "Route added successfully with ID: " + added_route.id},
        status_code=200,
    )


@spec_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/routes/{route_id}",
    tags=["specs"],
)
async def delete_route(
    user_id: str,
    app_id: str,
    spec_id: str,
    route_id: str,
):
    """
    Delete a specific route by its ID from a specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    # Delete the route from the spec
    await codex.requirements.database.delete_route_from_module(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        route_id=route_id,
    )

    return JSONResponse(
        content={"message": "Route deleted successfully"},
        status_code=200,
    )


@spec_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/routes/{route_id}/params",
    tags=["specs"],
)
async def add_param_to_route(
    user_id: str,
    app_id: str,
    spec_id: str,
    route_id: str,
    param: ObjectFieldModel,
    io: Literal["request", "response"],
):
    """
    Add a new parameter to a specific route by its ID in a specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    # Add the param to the route
    new = await codex.requirements.database.add_parameter_to_route(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        route_id=route_id,
        param=param,
        io=io,
    )

    return JSONResponse(
        content={"message": "Param added successfully", "param_id": new.id},
        status_code=200,
    )


@spec_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/routes/{route_id}/params/{param_id}",
    tags=["specs"],
)
async def delete_param_from_route(
    user_id: str,
    app_id: str,
    spec_id: str,
    route_id: str,
    param_id: str,
):
    """
    Delete a specific parameter by its ID from a route by its ID in a specification by its ID for a given application and user.
    """
    # Check that the spec exists, and implicitly that the user and app exist
    spec = await codex.requirements.database.get_specification(user_id, app_id, spec_id)
    if not spec:
        return JSONResponse(
            content={"error": "Specification not found"},
            status_code=404,
        )

    # Delete the param from the route
    await codex.requirements.database.delete_parameter_from_route(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        route_id=route_id,
        param_id=param_id,
    )

    return JSONResponse(
        content={"message": "Param deleted successfully"},
        status_code=200,
    )


@spec_router.delete("/user/{user_id}/apps/{app_id}/specs/{spec_id}", tags=["specs"])
async def delete_spec(user_id: str, app_id: str, spec_id: str):
    """
    Delete a specific specification by its ID for a given application and user.
    """
    await codex.requirements.database.delete_specification(spec_id)
    return JSONResponse(
        content={"message": "Specification deleted successfully"},
        status_code=200,
    )


@spec_router.get(
    "/user/{user_id}/apps/{app_id}/specs/",
    response_model=SpecificationsListResponse,
    tags=["specs"],
)
async def list_specs(
    user_id: str,
    app_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all specifications for a given application and user.
    """
    specs = await codex.requirements.database.list_specifications(
        user_id, app_id, page, page_size
    )
    return specs
