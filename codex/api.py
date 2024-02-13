import json
import logging

from fastapi import APIRouter, Path, Query, Response

import codex.database
from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    UserResponse,
    UsersListResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

core_routes = APIRouter()


# User endpoints
@core_routes.get("/discord/{discord_id}", response_model=UserResponse, tags=["users"])
async def get_discord_user(discord_id: int):
    """
    This is intended to be used by the Discord bot to retrieve user information.
    The user_id that is retrived can then be used for other API calls.
    """
    try:
        user = await codex.database.get_or_create_user_by_discord_id(discord_id)
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


@core_routes.get("/user/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(
    user_id: int = Path(..., description="The unique identifier of the user"),
):
    """
    Retrieve a user by their unique identifier.
    """
    try:
        user = await codex.database.get_user(user_id)
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


@core_routes.put("/user/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(user_id: int, user_update: UserUpdate):
    """
    Update a user's information by their unique identifier.
    """
    try:
        user = await codex.database.update_user(user_id, user_update)
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


@core_routes.get("/user/", response_model=UsersListResponse, tags=["users"])
async def list_users(
    page: int | None = Query(1, ge=1),
    page_size: int | None = Query(10, ge=1),
):
    """
    List all users.
    """
    try:
        users = await codex.database.list_users(page, page_size)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return Response(
            content=json.dumps({"error": f"Error listing users, {e}"}),
            status_code=500,
            media_type="application/json",
        )


# Apps endpoints
@core_routes.get(
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
        app_response = await codex.database.get_app_by_id(user_id, app_id)
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


@core_routes.post(
    "/user/{user_id}/apps/", response_model=ApplicationResponse, tags=["apps"]
)
async def create_app(user_id: int, app: ApplicationCreate):
    """
    Create a new application for a user.
    """
    try:
        app_response = await codex.database.create_app(user_id, app)
        return app_response
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        return Response(
            content=json.dumps({"error": f"Error creating application: {e}"}),
            status_code=500,
            media_type="application/json",
        )


@core_routes.delete("/user/{user_id}/apps/{app_id}", tags=["apps"])
async def delete_app(user_id: int, app_id: int):
    """
    Delete a specific application by its ID for a given user.
    """
    try:
        await codex.database.delete_app(user_id, app_id)
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


@core_routes.get(
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
        apps_response = await codex.database.list_apps(user_id, page, page_size)
        return apps_response
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return Response(
            content=json.dumps({"error": f"Error listing applications: {e}"}),
            status_code=500,
            media_type="application/json",
        )
