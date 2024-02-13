import json
import logging

from fastapi import APIRouter, Query, Response
from fastapi.responses import FileResponse

import codex.database
import codex.deploy.database
from codex.api_model import DeploymentResponse, DeploymentsListResponse, Indentifiers

logger = logging.getLogger(__name__)

deployment_router = APIRouter()


# deployments endpoints
@deployment_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
async def create_deployment(
    user_id: int,
    app_id: int,
    spec_id: int,
    deliverable_id: int,
):
    """
    Create a new deployment with the provided zip file.
    """
    ids = Indentifiers(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        completed_app_id=deliverable_id,
    )
    
    # File upload handling and metadata storage implementation goes here
    return Response(
        content=json.dumps(
            {"error": "Creating a new deployment is not yet implemented."}
        ),
        status_code=500,
        media_type="application/json",
    )


@deployment_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
async def get_deployment(
    user_id: int, app_id: int, spec_id: int, deliverable_id: int, deployment_id: int
):
    """
    Retrieve metadata about a specific deployment.
    """
    try:
        deployment = await codex.deploy.database.get_deployment(
            deployment_id=deployment_id
        )
        return deployment
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )


@deployment_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    tags=["deployments"],
)
async def delete_deployment(
    user_id: int, app_id: int, spec_id: int, deliverable_id: int, deployment_id: int
):
    """
    Delete a specific deployment.
    """
    try:
        await codex.deploy.database.delete_deployment(deployment_id=deployment_id)
        return Response(
            content=json.dumps({"message": "Deployment deleted successfully"}),
            status_code=200,
            media_type="application/json",
        )
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )


@deployment_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentsListResponse,
    tags=["deployments"],
)
async def list_deployments(
    user_id: int,
    app_id: int,
    spec_id: int,
    deliverable_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all deployments for a specific deliverable.
    """
    try:
        deployements = await codex.deploy.database.list_deployments(
            user_id=user_id,
            deliverable_id=deliverable_id,
            page=page,
            page_size=page_size,
        )
        return deployements
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )


@deployment_router.get("/deployments/{deployment_id}/download", tags=["deployments"])
async def download_deployment(deployment_id: int):
    """
    Download the zip file for a specific deployment.
    """
    deployment_details = await codex.deploy.database.get_deployment(
        deployment_id=deployment_id
    )
    logger.info(f"Downloading deployment: {deployment_details}")
    file_path = "path/to/deployment.zip"  # Placeholder path
    return FileResponse(path=file_path, filename="deployment.zip")
