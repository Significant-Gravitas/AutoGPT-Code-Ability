import base64
import io
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from prisma.models import CompletedApp
from prisma.types import (
    APIRouteSpecArgsFromCompiledRouteRecursive2,
    APIRouteSpecIncludeFromAPIRouteSpecRecursive3,
    CompiledRouteIncludeFromCompiledRouteRecursive1,
    CompletedAppInclude,
    FindManyCompiledRouteArgsFromCompletedApp,
    ObjectTypeArgsFromAPIRouteSpecRecursive4,
)

from codex.common.database import INCLUDE_FUNC
import codex.database
import codex.deploy.agent as deploy_agent
import codex.deploy.database
from codex.api_model import DeploymentResponse, DeploymentsListResponse, Identifiers

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
):
    """
    Create a new deployment with the provided zip file.
    """
    try:
        include = CompletedAppInclude(
            CompiledRoutes=FindManyCompiledRouteArgsFromCompletedApp(
                include=CompiledRouteIncludeFromCompiledRouteRecursive1(
                    ApiRouteSpec=APIRouteSpecArgsFromCompiledRouteRecursive2(
                        include=APIRouteSpecIncludeFromAPIRouteSpecRecursive3(
                            RequestObject=ObjectTypeArgsFromAPIRouteSpecRecursive4(
                                **{
                                    "include": {
                                        "Fields": {"include": {"RelatedTypes": True}}
                                    }
                                }
                            ),
                            ResponseObject=ObjectTypeArgsFromAPIRouteSpecRecursive4(
                                **{
                                    "include": {
                                        "Fields": {"include": {"RelatedTypes": True}}
                                    }
                                }
                            ),
                        )
                    ),
                    RootFunction=INCLUDE_FUNC,
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

        deployment = await deploy_agent.create_deployment(ids, completedApp)

        return DeploymentResponse(
            id=deployment.id,
            created_at=deployment.createdAt,
            file_name=deployment.fileName,
            file_size=deployment.fileSize,
        )
    except Exception as e:
        logger.exception(f"Error creating deployment: {e}")
        # File upload handling and metadata storage implementation goes here
        return Response(
            content=json.dumps(
                {"error": "Error creating deployment", "details": str(e)}
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
    user_id: str, app_id: str, spec_id: str, deliverable_id: str, deployment_id: str
):
    """
    Retrieve metadata about a specific deployment.
    """
    try:
        deployment = await codex.deploy.database.get_deployment(
            deployment_id=deployment_id
        )
        return DeploymentResponse(
            id=deployment.id,
            created_at=deployment.createdAt,
            file_name=deployment.fileName,
            file_size=deployment.fileSize,
        )
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
    user_id: str, app_id: str, spec_id: str, deliverable_id: str, deployment_id: str
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
    try:
        file_bytes = base64.b64decode(str(deployment_details.fileBytes))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decoding file content: {str(e)}"
        )

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
