import json
import logging

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse

import codex.database
import codex.requirements.agent
import codex.requirements.blocks.ai_endpoint
import codex.requirements.database
from codex.api_model import (
    Identifiers,
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
            content=json.dumps({"error": "Specification not found"}),
            status_code=404,
        )


@spec_router.put(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}",
    response_model=SpecificationResponse,
    tags=["specs"],
)
async def update_spec(
    user_id: str,
    app_id: str,
    spec_id: str,
    spec_update: SpecificationResponse,
):
    """
    TODO: This needs to be implemented
    Update a specific specification by its ID for a given application and user.
    """
    return JSONResponse(
        content=json.dumps(
            {"error": "Updating a specification is not yet implemented."}
        ),
        status_code=400,
    )


@spec_router.delete("/user/{user_id}/apps/{app_id}/specs/{spec_id}", tags=["specs"])
async def delete_spec(user_id: str, app_id: str, spec_id: str):
    """
    Delete a specific specification by its ID for a given application and user.
    """
    await codex.requirements.database.delete_specification(spec_id)
    return JSONResponse(
        content=json.dumps({"message": "Specification deleted successfully"}),
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
