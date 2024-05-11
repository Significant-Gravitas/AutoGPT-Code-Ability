import base64
import logging
import os

from langsmith import traceable
from prisma.models import CompletedApp, Deployment, Specification
from prisma.types import DeploymentCreateInput

from codex.api_model import Identifiers
from codex.deploy.infrastructure import create_cloud_db
from codex.deploy.model import Settings
from codex.deploy.packager import create_remote_repo, create_zip_file
from codex.develop.compile import create_bundle_code

logger = logging.getLogger(__name__)


@traceable
async def create_deployment(
    ids: Identifiers,
    completedApp: CompletedApp,
    spec: Specification,
    settings: Settings,
) -> Deployment:
    deployment_type = (
        create_local_deployment
        if (os.getenv("RUN_ENV", default="local") == "local" or settings.zipfile)
        else create_cloud_deployment
    )
    deployment = await deployment_type(ids, completedApp, spec, settings)

    return deployment


@traceable
async def create_local_deployment(
    ids: Identifiers,
    completedApp: CompletedApp,
    spec: Specification,
    settings: Settings,
) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = await create_bundle_code(completedApp, spec)

    zip_file = await create_zip_file(app, spec)
    file_name = completedApp.name.replace(" ", "_")
    trunc_user_id = ids.user_id[-6:]
    trunc_deliverable_id = ids.completed_app_id[-6:]
    unique_prefix = f"{trunc_user_id}_{file_name}_{trunc_deliverable_id}"
    try:
        base64.b64encode(zip_file)
        logger.info(
            f"Creating deployment for {completedApp.name} with repo ID {unique_prefix}"
        )
        encoded_file_bytes = base64.b64encode(zip_file).decode("utf-8")
        deployment = await Deployment.prisma().create(
            data=DeploymentCreateInput(
                CompletedApp={"connect": {"id": completedApp.id}},
                User={"connect": {"id": ids.user_id}},
                fileName=f"{file_name}.zip",
                fileSize=len(zip_file),
                # I need to do this as the Base64 type in prisma is not working
                fileBytes=encoded_file_bytes,  # type: ignore
                dbName=f"{unique_prefix}_db",
                dbUser=f"{unique_prefix}_user",
                repo=f"{unique_prefix}_repo",
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment


@traceable
async def create_cloud_deployment(
    ids: Identifiers,
    completedApp: CompletedApp,
    spec: Specification,
    settings: Settings,
) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = await create_bundle_code(completedApp, spec)

    repo = await create_remote_repo(app, spec, settings.hosted)
    completedApp.name.replace(" ", "_")
    file_name = completedApp.name.replace(" ", "_")
    trunc_user_id = ids.user_id[-6:]
    trunc_deliverable_id = ids.completed_app_id[-6:]
    unique_prefix = f"{trunc_user_id}_{file_name}_{trunc_deliverable_id}"
    db_name = f"{unique_prefix}_db"
    db_username = f"{unique_prefix}_user"

    if settings.hosted and os.getenv("HOSTED_DEPLOYMENT") == "google":
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
