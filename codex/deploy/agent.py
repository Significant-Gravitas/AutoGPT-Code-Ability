import logging

from prisma.models import CompletedApp, Deployment
from prisma.types import DeploymentCreateInput

from codex.api_model import Identifiers
from codex.deploy.packager import create_remote_repo
from codex.develop.compile import create_server_code

logger = logging.getLogger(__name__)


async def create_deployment(ids: Identifiers, completedApp: CompletedApp) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = await create_server_code(completedApp)

    repo = await create_remote_repo(app)
    completedApp.name.replace(" ", "_")

    try:
        logger.info(f"Creating deployment for {completedApp.name}")
        deployment = await Deployment.prisma().create(
            data=DeploymentCreateInput(
                CompletedApp={"connect": {"id": completedApp.id}},
                User={"connect": {"id": ids.user_id}},
                repo=repo,
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment
