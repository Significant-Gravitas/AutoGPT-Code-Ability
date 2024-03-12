import base64
import logging

from prisma.models import CompletedApp, Deployment
from prisma.types import DeploymentCreateInput

from codex.api_model import Identifiers
from codex.deploy.packager import create_zip_file
from codex.develop.compile import create_server_code

logger = logging.getLogger(__name__)


async def create_deployment(ids: Identifiers, completedApp: CompletedApp) -> Deployment:
    if not ids.user_id:
        raise ValueError("User ID is required to create a deployment")

    app = create_server_code(completedApp)

    zip_file = create_zip_file(app)
    file_name = completedApp.name.replace(" ", "_")

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
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment
