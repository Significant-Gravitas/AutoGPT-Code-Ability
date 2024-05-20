import logging

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

import codex.database
from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    UserResponse,
    UsersListResponse,
)

logger = logging.getLogger(__name__)

core_routes = APIRouter()


# User endpoints
@core_routes.post("/user", response_model=UserResponse, tags=["users"])
async def get_or_create_user(cloud_services_id: str, discord_id: str):
    """
    This is intended to be used by the Discord bot to retrieve user information.
    The user_id that is retrived can then be used for other API calls.
    """
    user = await codex.database.get_or_create_user_by_cloud_services_id_and_discord_id(
        cloud_services_id=cloud_services_id, discord_id=discord_id
    )
    return UserResponse(
        id=user.id,
        cloud_services_id=user.cloudServicesId,
        discord_id=user.discordId,
        createdAt=user.createdAt,
        role=user.role,
    )


@core_routes.get("/user/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(
    user_id: str = Path(..., description="The unique identifier of the user"),
):
    """
    Retrieve a user by their unique identifier.
    """
    user = await codex.database.get_user(user_id)
    return UserResponse(
        id=user.id,
        cloud_services_id=user.cloudServicesId,
        discord_id=user.discordId,
        createdAt=user.createdAt,
        role=user.role,
    )


@core_routes.get("/user/", response_model=UsersListResponse, tags=["users"])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all users.
    """
    users = await codex.database.list_users(page, page_size)
    return users


# Apps endpoints
@core_routes.get(
    "/user/{user_id}/apps/{app_id}", response_model=ApplicationResponse, tags=["apps"]
)
async def get_app(
    user_id: str = Path(..., description="The unique identifier of the user"),
    app_id: str = Path(..., description="The unique identifier of the application"),
):
    """
    Retrieve a specific application by its ID for a given user.
    """
    app_response = await codex.database.get_app_response_by_id(user_id, app_id)
    if app_response:
        return app_response
    else:
        return JSONResponse(
            content={"error": "Application not found"},
            status_code=404,
        )


@core_routes.post(
    "/user/{user_id}/apps/", response_model=ApplicationResponse, tags=["apps"]
)
async def create_app(user_id: str, app: ApplicationCreate):
    """
    Create a new application for a user.
    """
    app_response = await codex.database.create_app(user_id, app)
    return app_response


@core_routes.delete("/user/{user_id}/apps/{app_id}", tags=["apps"])
async def delete_app(user_id: str, app_id: str):
    """
    Delete a specific application by its ID for a given user.
    """
    await codex.database.delete_app(user_id, app_id)
    return JSONResponse(
        content={"message": "Application deleted successfully"},
        status_code=200,
    )


@core_routes.get(
    "/user/{user_id}/apps/", response_model=ApplicationsListResponse, tags=["apps"]
)
async def list_apps(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    """
    List all applications for a given user.
    """
    apps_response = await codex.database.list_apps(user_id, page, page_size)
    return apps_response
