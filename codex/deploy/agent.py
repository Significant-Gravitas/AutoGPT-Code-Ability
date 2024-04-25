import base64
import logging
import os
import uuid

from prisma.models import CompletedApp, Deployment, Specification
from prisma.types import DeploymentCreateInput

from codex.api_model import Identifiers
from codex.deploy.packager import create_remote_repo, create_zip_file
from codex.develop.compile import create_server_code
from codex.deploy.infrastructure import create_cloud_db

logger = logging.getLogger(__name__)


async def create_deployment(
    ids: Identifiers, completedApp: CompletedApp, spec: Specification
) -> Deployment:
    environment: str = os.getenv("RUN_ENV").lower()
    if environment == "local":
        deployment = await create_local_deployment(ids, completedApp, spec)
        return deployment

    deployment = await create_cloud_deployment(ids, completedApp, spec)
    return deployment


async def create_local_deployment(
    ids: Identifiers, completedApp: CompletedApp, spec: Specification
) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = await create_server_code(completedApp, spec)

    zip_file = await create_zip_file(app, spec)
    file_name = completedApp.name.replace(" ", "_")
    repo = str(uuid.uuid4())
    try:
        base64.b64encode(zip_file)
        logger.info(f"Creating deployment for {completedApp.name}")
        encoded_file_bytes = base64.b64encode(zip_file).decode("utf-8")
        deployment = await Deployment.prisma().create(
            data=DeploymentCreateInput(
                CompletedApp={"connect": {"id": completedApp.id}},
                User={"connect": {"id": ids.user_id}},
                fileName=f"{file_name}.zip",
                fileSize=len(zip_file),
                # I need to do this as the Base64 type in prisma is not working
                fileBytes=encoded_file_bytes,  # type: ignore
                dbName=repo+"_db",
                dbUser=repo+"_repo",
                repo=repo,  # repo has unique constraint so we need to generate a random string
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment


async def create_cloud_deployment(
    ids: Identifiers, completedApp: CompletedApp, spec: Specification
) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = await create_server_code(completedApp, spec)

    repo = await create_remote_repo(app, spec)
    completedApp.name.replace(" ", "_")
    db_name, db_username = await create_cloud_db(repo)

    try:
        logger.info(f"Creating deployment for {completedApp.name}")
        deployment = await Deployment.prisma().create(
            data=DeploymentCreateInput(
                CompletedApp={"connect": {"id": completedApp.id}},
                User={"connect": {"id": ids.user_id}},
                repo=repo,
                dbName=db_name,
                dbUser=db_username,
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment
