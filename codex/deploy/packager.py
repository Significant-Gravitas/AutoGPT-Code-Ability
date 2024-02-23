import logging
import os
import tempfile
import zipfile
from collections import defaultdict
from typing import List

from prisma.models import Package

from codex.deploy.model import Application

logger = logging.getLogger(__name__)


def generate_requirements_txt(packages: List[Package]) -> str:
    resolved_packages = defaultdict(list)

    # Aggregate versions and specifiers for each package
    for package in packages:
        resolved_packages[package.packageName].append(
            (package.version, package.specifier)
        )

    requirements = []
    for package, versions_specifiers in resolved_packages.items():
        # Handle different cases of version and specifier here
        # For simplicity, we just pick the first version and specifier encountered
        # More complex logic might be needed depending on the requirement
        version, specifier = versions_specifiers[0]
        if version and specifier:
            requirement = f"{package}{specifier}{version}"
        elif version:
            requirement = f"{package}=={version}"
        else:
            requirement = package
        requirements.append(requirement)

    return "\n".join(requirements)


def create_zip_file(application: Application) -> bytes:
    """
    Creates a zip file from the application
    Args:
        application (Application): The application to be zipped

    Returns:
        bytes: The zipped file
    """
    logger.info("Creating zip file")
    assert application.completed_app, "Application must have a completed app"
    assert (
        application.completed_app.CompiledRoutes
    ), "Application must have at least one compiled route"
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

            requirements_file_path = os.path.join(app_dir, "requirements.txt")
            packages = ""
            if application.packages:
                packages = generate_requirements_txt(application.packages)

            with open(requirements_file_path, "w") as requirements_file:
                requirements_file.write(packages)

            for compiled_route in application.completed_app.CompiledRoutes:
                service_file_path = os.path.join(app_dir, compiled_route.fileName)
                with open(service_file_path, "w") as service_file:
                    service_file.write(compiled_route.compiledCode)
            logger.info("Created server code")
            # Create a zip file of the directory
            zip_file_path = os.path.join(app_dir, "server.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == "server.zip":
                            continue
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, temp_dir))

            logger.info("Created zip file")
            # Read and return the bytes of the zip file
            with open(zip_file_path, "rb") as zipf:
                zip_bytes = zipf.read()

            return zip_bytes
    except Exception as e:
        logger.exception(e)
        raise e
