import json
import logging

from fastapi import FastAPI, File, Path, Query, Response, UploadFile
from fastapi.responses import FileResponse
from prisma import Prisma

import codex.database
from codex.api_models import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    DeliverableResponse,
    DeliverablesListResponse,
    DeploymentResponse,
    DeploymentsListResponse,
    SpecificationResponse,
    SpecificationsListResponse,
    UserResponse,
    UsersListResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)

app = FastAPI(
    title="Codex",
    description="Codex is a platform for creating, deploying, and managing web applications.",
    summary="Codex API",
    version="0.1",
)


# User endpoints


@app.get("/discord/{discord_id}", response_model=UserResponse, tags=["users"])
def get_discord_user(discord_id: int):
    """
    Retrieve a user by their Discord ID.
    """
    try:
        user = codex.database.get_or_create_user_by_discord_id(discord_id, db_client)
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
            status_code=404,
            media_type="application/json",
        )


@app.get("/user/{user_id}", response_model=UserResponse, tags=["users"])
def get_user(user_id: int = Path(..., description="The unique identifier of the user")):
    """
    Retrieve a user by their unique identifier.
    """
    try:
        user = codex.database.get_user(user_id, db_client)
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
            status_code=404,
            media_type="application/json",
        )


@app.put("/user/{user_id}", response_model=UserResponse, tags=["users"])
def update_user(user_id: int, user_update: UserUpdate):
    """
    Update a user's information by their unique identifier.
    """
    try:
        user = codex.database.update_user(user_id, user_update, db_client)
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
            status_code=404,
            media_type="application/json",
        )


@app.get("/user/", response_model=UsersListResponse, tags=["users"])
def list_users(
    page: int | None = Query(1, ge=1),
    page_size: int | None = Query(10, ge=1),
):
    """
    List all users.
    """
    try:
        users = codex.database.list_users(page, page_size, db_client)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return Response(
            content=json.dumps({"error": f"Error listing users, {e}"}),
            status_code=404,
            media_type="application/json",
        )


# Apps endpoints
@app.get(
    "/user/{user_id}/apps/{app_id}", response_model=ApplicationResponse, tags=["apps"]
)
def get_app(
    user_id: int = Path(..., description="The unique identifier of the user"),
    app_id: int = Path(..., description="The unique identifier of the application"),
):
    """
    Retrieve a specific application by its ID for a given user.
    """
    # Implementation goes here
    return {"user_id": user_id, "app_id": app_id, "action": "get_app"}


@app.post("/user/{user_id}/apps/", response_model=ApplicationResponse, tags=["apps"])
def create_app(user_id: int, app: ApplicationCreate):
    """
    Create a new application for a user.
    """
    # Implementation goes here
    return {"user_id": user_id, "action": "create_app"}


@app.delete("/user/{user_id}/apps/{app_id}", tags=["apps"])
def delete_app(user_id: int, app_id: int):
    """
    Delete a specific application by its ID for a given user.
    """
    # Implementation goes here
    return {"user_id": user_id, "app_id": app_id, "action": "delete_app"}


@app.get(
    "/user/{user_id}/apps/", response_model=ApplicationsListResponse, tags=["apps"]
)
def list_apps(user_id: int):
    """
    List all applications for a given user.
    """
    # Implementation goes here
    return {"user_id": user_id, "action": "list_apps"}


# Specs endpoints
@app.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}",
    response_model=SpecificationResponse,
    tags=["specs"],
)
def get_spec(user_id: int, app_id: int, spec_id: int):
    """
    Retrieve a specific specification by its ID for a given application and user.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "action": "get_spec",
    }


@app.post(
    "/user/{user_id}/apps/{app_id}/specs/",
    tags=["specs"],
    response_model=SpecificationResponse,
)
def create_spec(user_id: int, app_id: int):
    """
    Create a new specification for a given application and user.
    """
    # Implementation goes here
    return {"user_id": user_id, "app_id": app_id, "action": "create_spec"}


@app.put(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}",
    tags=["specs"],
    response_model=SpecificationResponse,
)
def update_spec(user_id: int, app_id: int, spec_id: int):
    """
    Update a specific specification by its ID for a given application and user.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "action": "update_spec",
    }


@app.delete("/user/{user_id}/apps/{app_id}/specs/{spec_id}", tags=["specs"])
def delete_spec(user_id: int, app_id: int, spec_id: int):
    """
    Delete a specific specification by its ID for a given application and user.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "action": "delete_spec",
    }


@app.get(
    "/user/{user_id}/apps/{app_id}/specs/",
    response_model=SpecificationsListResponse,
    tags=["specs"],
)
def list_specs(user_id: int, app_id: int):
    """
    List all specifications for a given application and user.
    """
    # Implementation goes here
    return {"user_id": user_id, "app_id": app_id, "action": "list_specs"}


# Deliverables endpoints
@app.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    response_model=DeliverableResponse,
    tags=["deliverables"],
)
def get_deliverable(user_id: int, app_id: int, spec_id: int, deliverable_id: int):
    """
    Retrieve a specific deliverable (completed app) including its compiled routes by ID.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "action": "get_deliverable",
    }


@app.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    tags=["deliverables"],
    response_model=DeliverableResponse,
)
def create_deliverable(user_id: int, app_id: int, spec_id: int):
    """
    Create a new deliverable (completed app) for a specific specification.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "action": "create_deliverable",
    }


@app.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}",
    tags=["deliverables"],
)
def delete_deliverable(user_id: int, app_id: int, spec_id: int, deliverable_id: int):
    """
    Delete a specific deliverable (completed app) by ID.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "action": "delete_deliverable",
    }


@app.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/",
    response_model=DeliverablesListResponse,
    tags=["deliverables"],
)
def list_deliverables(user_id: int, app_id: int, spec_id: int):
    """
    List all deliverables (completed apps) for a specific specification.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "action": "list_deliverables",
    }


# deployments endpoints
@app.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
def get_deployment(
    user_id: int, app_id: int, spec_id: int, deliverable_id: int, deployment_id: int
):
    """
    Retrieve metadata about a specific deployment.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "deployment_id": deployment_id,
        "action": "get_deployment",
    }


@app.post(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentResponse,
    tags=["deployments"],
)
def create_deployment(
    user_id: int,
    app_id: int,
    spec_id: int,
    deliverable_id: int,
    file: UploadFile = File(...),
):
    """
    Create a new deployment with the provided zip file.
    """
    # File upload handling and metadata storage implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "action": "create_deployment",
    }


@app.delete(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}",
    tags=["deployments"],
)
def delete_deployment(
    user_id: int, app_id: int, spec_id: int, deliverable_id: int, deployment_id: int
):
    """
    Delete a specific deployment.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "deployment_id": deployment_id,
        "action": "delete_deployment",
    }


@app.get(
    "/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/",
    response_model=DeploymentsListResponse,
    tags=["deployments"],
)
def list_deployments(user_id: int, app_id: int, spec_id: int, deliverable_id: int):
    """
    List all deployments for a specific deliverable.
    """
    # Implementation goes here
    return {
        "user_id": user_id,
        "app_id": app_id,
        "spec_id": spec_id,
        "deliverable_id": deliverable_id,
        "action": "list_deployments",
    }


@app.get("/deployments/{deployment_id}/download", tags=["deployments"])
def download_deployment(deployment_id: int):
    """
    Download the zip file for a specific deployment.
    """
    # Locate the file based on deployment_id, ensure it exists, and return a FileResponse
    file_path = "path/to/deployment.zip"  # Placeholder path
    return FileResponse(path=file_path, filename="deployment.zip")
