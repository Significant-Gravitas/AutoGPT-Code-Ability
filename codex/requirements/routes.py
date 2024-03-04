import json
import logging

from fastapi import APIRouter, Query, Response

import codex.database
import codex.requirements.database
from codex.api_model import (
    Identifiers,
    SpecificationResponse,
    SpecificationsListResponse,
)
from codex.interview.database import get_interview
from codex.requirements.agent import generate_requirements

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
    try:
        app = await codex.database.get_app_by_id(user_id, app_id)
        user = await codex.database.get_user(user_id)
        ids = Identifiers(
            user_id=user_id,
            app_id=app_id,
            interview_id=interview_id,
            cloud_services_id=user.cloudServicesId if user else "",
        )
        interview = await get_interview(
            user_id=ids.user_id, app_id=ids.app_id, interview_id=interview_id
        )
        if not interview:
            return Response(
                content=json.dumps({"error": "Interview not found"}),
                status_code=404,
                media_type="application/json",
            )
        new_spec = await generate_requirements(ids, interview.task)
        return SpecificationResponse.from_specification(new_spec)
    except Exception as e:
        logger.error(f"Error creating a new specification: {e}")
        return Response(
            content=json.dumps(
                {"error": f"Error creating a new specification: {str(e)}"}
            ),
            status_code=500,
            media_type="application/json",
        )


@spec_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}",
    response_model=SpecificationResponse,
    tags=["specs"],
)
async def get_spec(user_id: str, app_id: str, spec_id: str):
    """
    Retrieve a specific specification by its ID for a given application and user.
    """
    try:
        specification = await codex.requirements.database.get_specification(
            user_id, app_id, spec_id
        )
        if specification:
            return SpecificationResponse.from_specification(specification)
        else:
            return Response(
                content=json.dumps({"error": "Specification not found"}),
                status_code=404,
                media_type="application/json",
            )
    except Exception as e:
        logger.error(f"Error retrieving specification: {e}")
        return Response(
            content=json.dumps({"error": "Error retrieving specification"}),
            status_code=500,
            media_type="application/json",
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
    return Response(
        content=json.dumps(
            {"error": "Updating a specification is not yet implemented."}
        ),
        status_code=500,
        media_type="application/json",
    )


@spec_router.delete("/user/{user_id}/apps/{app_id}/specs/{spec_id}", tags=["specs"])
async def delete_spec(user_id: str, app_id: str, spec_id: str):
    """
    Delete a specific specification by its ID for a given application and user.
    """
    try:
        await codex.requirements.database.delete_specification(spec_id)
        return Response(
            content=json.dumps({"message": "Specification deleted successfully"}),
            status_code=200,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Error deleting specification: {e}")
        return Response(
            content=json.dumps({"error": "Error deleting specification"}),
            status_code=500,
            media_type="application/json",
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
    try:
        specs = await codex.requirements.database.list_specifications(
            user_id, app_id, page, page_size
        )
        return specs
    except Exception as e:
        logger.error(f"Error listing specifications: {e}")
        return Response(
            content=json.dumps({"error": "Error listing specifications"}),
            status_code=500,
            media_type="application/json",
        )
