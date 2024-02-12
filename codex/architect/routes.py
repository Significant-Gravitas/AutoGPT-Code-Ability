import json
import logging

from fastapi import APIRouter, Query, Response

import codex.architect.agent as architect_agent
import codex.database
import codex.delivery.agent as delivery_agent
import codex.developer.agent as developer_agent
from codex.api_model import DeliverableResponse, DeliverablesListResponse

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

delivery_router = APIRouter()


# Deliverables endpoints
@delivery_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    tags=["deliverables"],
    response_model=DeliverableResponse,
)
async def create_deliverable(user_id: int, app_id: int, spec_id: int):
    """
    Create a new deliverable (completed app) for a specific specification.
    """
    specification = await codex.database.get_specification(user_id, app_id, spec_id)
    if specification:
        return specification
    else:
        return Response(
            content=json.dumps({"error": "Specification not found"}),
            status_code=500,
            media_type="application/json",
        )
    # Architect agent creates the code graphs for the requirements
    graphs = architect_agent.create_code_graphs(specification)
    # Developer agent writes the code for the code graphs
    completed_graphs = developer_agent.write_code_graphs(graphs)
    # Delivery Agent builds the code and delivers it to the user
    application = delivery_agent.compile_application(specification, completed_graphs)

    return Response(
        content=json.dumps(
            {"error": "Creating a new deliverable is not yet implemented."}
        ),
        status_code=500,
        media_type="application/json",
    )


@delivery_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    tags=["deliverables"],
)
async def get_deliverable(user_id: int, app_id: int, spec_id: int, deliverable_id: int):
    """
    Retrieve a specific deliverable (completed app) including its compiled routes by ID.
    """
    try:
        deliverable = await codex.database.get_deliverable(
            user_id, app_id, spec_id, deliverable_id
        )
        return deliverable
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
    user_id: int, app_id: int, spec_id: int, deliverable_id: int
):
    """
    Delete a specific deliverable (completed app) by ID.
    """
    try:
        await codex.database.delete_deliverable(
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
    user_id: int,
    app_id: int,
    spec_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all deliverables (completed apps) for a specific specification.
    """
    try:
        deliverables = await codex.database.list_deliverables(
            user_id, app_id, spec_id, page, page_size
        )
        return deliverables
    except Exception as e:
        return Response(
            content=json.dumps({"error": f"Error listing deliverables: {str(e)}"}),
            status_code=500,
            media_type="application/json",
        )
