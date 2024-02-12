import json
import logging

from fastapi import FastAPI, Path, Query, Response
from fastapi.responses import FileResponse
from prisma import Prisma

import codex.database
from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    DeploymentResponse,
    DeploymentsListResponse,
    UserResponse,
    UsersListResponse,
    UserUpdate,
)
from codex.requirements.routes import spec_router
from codex.architect.routes import delivery_router

logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)

app = FastAPI(
    title="Codex",
    description="Codex is a platform for creating, deploying, and managing web applications.",
    summary="Codex API",
    version="0.1",
)


app.include_router(spec_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    await db_client.connect()


@app.on_event("shutdown")
async def shutdown():
    await db_client.disconnect()


# User endpoints
@app.get("/discord/{discord_id}", response_model=UserResponse, tags=["users"])
async def get_discord_user(discord_id: int):
    """
    This is intended to be used by the Discord bot to retrieve user information.
    The user_id that is retrived can then be used for other API calls.
    """
    try:
        user = await codex.database.get_or_create_user_by_discord_id(
            discord_id, db_client
        )
        return UserResponse(
            id=user.id,
            discord_id=user.discord_id,
            createdAt=user.createdAt,
            email=user.email,
            name=user.name,
            role=user.role,
        )
    except Exception as e:
        logger.error(f"Error retrieving user by discord id ({discord_id}): {e}")
        return Response(
            content=json.dumps({"error": "Error retrieving user by discord_id"}),
            status_code=500,
            media_type="application/json",
        )


@app.get("/user/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(
    user_id: int = Path(..., description="The unique identifier of the user"),
):
    """
    Retrieve a user by their unique identifier.
    """
    try:
        user = await codex.database.get_user(user_id, db_client)
        return UserResponse(
            id=user.id,
            discord_id=user.discord_id,
            createdAt=user.createdAt,
            email=user.email,
            name=user.name,
            role=user.role,
        )
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return Response(
            content=json.dumps({"error": f"Error retrieving user by id {e}"}),
            status_code=500,
            media_type="application/json",
        )


@app.put("/user/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(user_id: int, user_update: UserUpdate):
    """
    Update a user's information by their unique identifier.
    """
    try:
        user = await codex.database.update_user(user_id, user_update, db_client)
        return UserResponse(
            id=user.id,
            discord_id=user.discord_id,
            createdAt=user.createdAt,
            email=user.email,
            name=user.name,
            role=user.role,
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return Response(
            content=json.dumps({"error": f"Error updating user {e}"}),
            status_code=500,
            media_type="application/json",
        )


@app.get("/user/", response_model=UsersListResponse, tags=["users"])
async def list_users(
    page: int | None = Query(1, ge=1),
    page_size: int | None = Query(10, ge=1),
):
    """
    List all users.
    """
    try:
        users = await codex.database.list_users(page, page_size, db_client)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return Response(
            content=json.dumps({"error": f"Error listing users, {e}"}),
            status_code=500,
            media_type="application/json",
        )


# Apps endpoints
@app.get(
    "/user/{user_id}/apps/{app_id}", response_model=ApplicationResponse, tags=["apps"]
)
async def get_app(
    user_id: int = Path(..., description="The unique identifier of the user"),
    app_id: int = Path(..., description="The unique identifier of the application"),
):
    """
    Retrieve a specific application by its ID for a given user.
    """
    try:
        app_response = await codex.database.get_app_by_id(user_id, app_id, db_client)
        if app_response:
            return app_response
        else:
            return Response(
                content=json.dumps({"error": "Application not found"}),
                status_code=404,
                media_type="application/json",
            )
    except Exception as e:
        logger.error(f"Error retrieving application: {e}")
        return Response(
            content=json.dumps({"error": f"Error retrieving application: {e}"}),
            status_code=500,
            media_type="application/json",
        )


@app.post("/user/{user_id}/apps/", response_model=ApplicationResponse, tags=["apps"])
async def create_app(user_id: int, app: ApplicationCreate):
    """
    Create a new application for a user.
    """
    try:
        app_response = await codex.database.create_app(user_id, app, db_client)
        return app_response
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        return Response(
            content=json.dumps({"error": f"Error creating application: {e}"}),
            status_code=500,
            media_type="application/json",
        )


@app.delete("/user/{user_id}/apps/{app_id}", tags=["apps"])
async def delete_app(user_id: int, app_id: int):
    """
    Delete a specific application by its ID for a given user.
    """
    try:
        await codex.database.delete_app(user_id, app_id, db_client)
        return Response(
            content=json.dumps({"message": "Application deleted successfully"}),
            status_code=200,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Error deleting application: {e}")
        return Response(
            content=json.dumps({"error": f"Error deleting application: {e}"}),
            status_code=500,
            media_type="application/json",
        )


@app.get(
    "/user/{user_id}/apps/", response_model=ApplicationsListResponse, tags=["apps"]
)
async def list_apps(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all applications for a given user.
    """
    try:
        apps_response = await codex.database.list_apps(
            user_id, page, page_size, db_client
        )
        return apps_response
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return Response(
            content=json.dumps({"error": f"Error listing applications: {e}"}),
            status_code=500,
            media_type="application/json",
        )


# deployments endpoints
@app.post(
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
    # File upload handling and metadata storage implementation goes here
    return Response(
        content=json.dumps(
            {"error": "Creating a new deployment is not yet implemented."}
        ),
        status_code=500,
        media_type="application/json",
    )


@app.get(
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
        deployment = await codex.database.get_deployment(
            deployment_id=deployment_id, db_client=db_client
        )
        return deployment
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )


@app.delete(
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
        await codex.database.delete_deployment(
            deployment_id=deployment_id, db_client=db_client
        )
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


@app.get(
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
        deployements = await codex.database.list_deployments(
            user_id=user_id,
            deliverable_id=deliverable_id,
            page=page,
            page_size=page_size,
            db_client=db_client,
        )
        return deployements
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )


@app.get("/deployments/{deployment_id}/download", tags=["deployments"])
async def download_deployment(deployment_id: int):
    """
    Download the zip file for a specific deployment.
    """
    deployment_details = await codex.database.get_deployment(
        deployment_id=deployment_id, db_client=db_client
    )
    logger.info(f"Downloading deployment: {deployment_details}")
    file_path = "path/to/deployment.zip"  # Placeholder path
    return FileResponse(path=file_path, filename="deployment.zip")
