import logging
import os
import tempfile
import zipfile

from codex.delivery.model import Application

logger = logging.getLogger(__name__)


def create_zip_file(application: Application) -> bytes:
    """
    Creates a zip file from the application
    Args:
        application (Application): The application to be zipped

    Returns:
        bytes: The zipped file
    """
    logger.info("Creating zip file")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = os.path.join(temp_dir, "project")
            os.makedirs(app_dir, exist_ok=True)

            init_file_path = os.path.join(app_dir, "__init__.py")
            with open(init_file_path, "w") as init_file:
                init_file.write("")

            server_file_path = os.path.join(app_dir, "server.py")
            with open(server_file_path, "w") as server_file:
                server_file.write(application.server_code)

            for route_name, compiled_route in application.routes.items():
                service_file_path = os.path.join(
                    app_dir, compiled_route.service_file_name
                )
                with open(service_file_path, "w") as service_file:
                    service_file.write(compiled_route.service_code)

            # Create a zip file of the directory
            zip_file_path = os.path.join(app_dir, "server.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == "server.zip":
                            continue
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, temp_dir))

            # Read and return the bytes of the zip file
            with open(zip_file_path, "rb") as zipf:
                zip_bytes = zipf.read()

            return zip_bytes
    except Exception as e:
        logger.exception(e)
