import json
import logging

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

import codex.database
import codex.develop.agent as architect_agent
import codex.develop.database
import codex.requirements.database
from codex.api_model import (
    ApplicationCreate,
    DeliverableResponse,
    DeliverablesListResponse,
    Identifiers,
)
from codex.common.model import FunctionSpec
from codex.develop.model import FunctionResponse

logger = logging.getLogger(__name__)

delivery_router = APIRouter()


# Deliverables endpoints
@delivery_router.post(
    "/function/",
    tags=["deliverables"],
)
async def write_function(function_spec: FunctionSpec):
    # Create AutoGPT user

    user = await codex.database.get_or_create_user_by_cloud_services_id_and_discord_id(
        "AutoGPT", "AutoGPT"
    )
    # Create App for this function
    app = await codex.database.create_app_db(
        user.id,
        ApplicationCreate(
            name=function_spec.name, description=function_spec.description
        ),
    )

    ids = Identifiers(user_id=user.id, app_id=app.id)
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
            content=json.dumps({"error": "Specification not found"}),
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
        content=json.dumps({"message": "Deliverable deleted successfully"}),
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
