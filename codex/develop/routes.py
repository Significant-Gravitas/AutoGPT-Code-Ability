import json
import logging

from fastapi import APIRouter, Query, Response

import codex.database
import codex.develop.agent as architect_agent
import codex.develop.database
import codex.requirements.database
from codex.api_model import DeliverableResponse, DeliverablesListResponse, Identifiers

logger = logging.getLogger(__name__)

delivery_router = APIRouter()


# Deliverables endpoints
@delivery_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    tags=["deliverables"],
    response_model=DeliverableResponse,
)
async def create_deliverable(user_id: str, app_id: str, spec_id: str):
    """
    Create a new deliverable (completed app) for a specific specification.
    """
    try:
        specification = await codex.requirements.database.get_specification(
            user_id, app_id, spec_id
        )
        user = await codex.database.get_user(user_id)
        logger.info(f"Creating deliverable for {specification.name}")
        if specification:
            ids = Identifiers(
                user_id=user_id,
                cloud_services_id=user.cloudServicesId if user else "",
                app_id=app_id,
                spec_id=spec_id,
            )
            # Architect agent creates the code graphs for the requirements
            completed_app = await architect_agent.develop_application(
                ids, specification
            )

            return DeliverableResponse(
                id=completed_app.id,
                created_at=completed_app.createdAt,
                name=completed_app.name,
                description=completed_app.description,
            )
        else:
            return Response(
                content=json.dumps({"error": "Specification not found"}),
                status_code=500,
                media_type="application/json",
            )
    except Exception as e:
        logger.error(f"Error creating deliverable: {str(e)}")
        return Response(
            content=json.dumps({"error": f"Error creating deliverable: {str(e)}"}),
            status_code=500,
            media_type="application/json",
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
    try:
        deliverable = await codex.develop.database.get_deliverable(
            user_id, app_id, spec_id, deliverable_id
        )
        return DeliverableResponse(
            id=deliverable.id,
            created_at=deliverable.createdAt,
            name=deliverable.name,
            description=deliverable.description,
        )
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
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
    try:
        await codex.develop.database.delete_deliverable(
            user_id, app_id, spec_id, deliverable_id
        )
        return Response(
            content=json.dumps({"message": "Deliverable deleted successfully"}),
            status_code=200,
            media_type="application/json",
        )
    except Exception as e:
        return Response(
            content=json.dumps({"error": f"Error deleting deliverable: {str(e)}"}),
            status_code=500,
            media_type="application/json",
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
    List all deliverables (completed apps) for a specific specification.
    """
    try:
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
    except Exception as e:
        return Response(
            content=json.dumps({"error": f"Error listing deliverables: {str(e)}"}),
            status_code=500,
            media_type="application/json",
        )
