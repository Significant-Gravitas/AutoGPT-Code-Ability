import base64
import io
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from prisma.models import CompletedApp
from prisma.types import (
    CompiledRouteIncludeFromCompiledRouteRecursive1,
    CompletedAppInclude,
    FindManyCompiledRouteArgsFromCompletedApp,
)

import codex.database
import codex.deploy.agent as deploy_agent
import codex.deploy.database
import codex.requirements.database
from codex.api_model import (
    DeploymentRequest,
    DeploymentResponse,
    DeploymentsListResponse,
    Identifiers,
)
from codex.common.database import INCLUDE_API_ROUTE, INCLUDE_FUNC
from codex.deploy.model import Settings

logger = logging.getLogger(__name__)

deployment_router = APIRouter()


# deployments endpoints
@deployment_router.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
async def create_deployment(
    user_id: str,
    app_id: str,
    spec_id: str,
    deliverable_id: str,
    deployment_details: Optional[DeploymentRequest] = None,
):
    """
    Create a new deployment with the provided zip file.
    """
    include = CompletedAppInclude(
        CompiledRoutes=FindManyCompiledRouteArgsFromCompletedApp(
            include=CompiledRouteIncludeFromCompiledRouteRecursive1(
                ApiRouteSpec=INCLUDE_API_ROUTE,  # type: ignore
                RootFunction=INCLUDE_FUNC,  # type: ignore
                Packages=True,
            )
        ),
    )
    completedApp = await CompletedApp.prisma().find_unique(
        where={"id": deliverable_id},
        include=include,
    )

    user = await codex.database.get_user(user_id)

    if not completedApp:
        raise ValueError(f"Completed app {deliverable_id} not found")

    logger.info(f"Creating deployment for {completedApp.name}")
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        spec_id=spec_id,
        completed_app_id=deliverable_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )

    spec = await codex.requirements.database.get_specification(
        user_id=user_id, app_id=app_id, spec_id=spec_id
    )

    deployment_settings: Settings | None = None

    if deployment_details is None:
        logger.info(f"No deployment settings provided for app {app_id}")
        deployment_settings = Settings(
            zipfile=False,
            githubRepo=True,
            hosted=True,
        )
    else:
        try:
            deployment_settings = Settings(
                zipfile=deployment_details.zip_file,
                githubRepo=deployment_details.github_repo,
                hosted=deployment_details.hosted,
            )
        except Exception as e:
            logger.error("error in deployment settings: %s", e)

    if deployment_settings is None:
        deployment_settings = Settings(
            zipfile=False,
            githubRepo=True,
            hosted=False,
        )

    deployment = await deploy_agent.create_deployment(
        ids, completedApp, spec, deployment_settings
    )

    return DeploymentResponse(
        id=deployment.id,
        created_at=deployment.createdAt,
        repo=deployment.repo if deployment.repo else "",
    )


@deployment_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
async def get_deployment(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str, deployment_id: str
):
    """
    Retrieve metadata about a specific deployment.
    """
    deployment = await codex.deploy.database.get_deployment(deployment_id=deployment_id)
    return DeploymentResponse(
        id=deployment.id,
        created_at=deployment.createdAt,
        repo=deployment.repo if deployment.repo else "",
    )


@deployment_router.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    tags=["deployments"],
)
async def delete_deployment(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str, deployment_id: str
):
    """
    Delete a specific deployment.
    """
    await codex.deploy.database.delete_deployment(deployment_id=deployment_id)
    return JSONResponse(
        content={"message": "Deployment deleted successfully"},
        status_code=200,
    )


@deployment_router.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentsListResponse,
    tags=["deployments"],
)
async def list_deployments(
    user_id: str,
    app_id: str,
    spec_id: str,
    deliverable_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all deployments for a specific deliverable.
    """
    deployements = await codex.deploy.database.list_deployments(
        user_id=user_id,
        deliverable_id=deliverable_id,
        page=page,
        page_size=page_size,
    )
    return deployements


@deployment_router.get("/deployments/{deployment_id}/download", tags=["deployments"])
async def download_deployment(deployment_id: str):
    """
    Download the zip file for a specific deployment.
    """
    # Retrieve deployment details, assuming this
    # returns an object that includes the file bytes
    deployment_details = await codex.deploy.database.get_deployment(
        deployment_id=deployment_id
    )
    if not deployment_details:
        raise HTTPException(status_code=404, detail="Deployment not found")

    logger.info(f"Downloading deployment: {deployment_id}")

    # Decode the base64-encoded file bytes
    file_bytes = base64.b64decode(str(deployment_details.fileBytes))

    # Convert the bytes to a BytesIO object for streaming
    file_stream = io.BytesIO(file_bytes)

    # Set the correct content-type for zip files
    headers = {
        "Content-Disposition": f"attachment; filename={deployment_details.fileName}"
    }

    # Return the streaming response
    return StreamingResponse(
        content=file_stream, media_type="application/zip", headers=headers
    )
