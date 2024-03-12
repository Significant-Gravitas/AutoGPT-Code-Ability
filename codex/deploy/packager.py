import datetime
import logging
import os
import tempfile
import zipfile
from typing import List

from pipreqs import pipreqs
from prisma.models import Package

from codex.deploy.model import Application

logger = logging.getLogger(__name__)


def generate_requirements_txt(
    packages: List[Package], pipreq_pacakages: List[str]
) -> str:
    requirements = set()

    for package in packages:
        requirements.add(package.packageName.replace("\n", "").strip())

    for package in pipreq_pacakages:
        requirements.add(package.replace("\n", "").strip())

    return "\n".join(sorted(requirements))


def create_prisma_scheama_file(application: Application) -> str:
    tables = []
    table_names = set()
    if (
        application.completed_app.CompiledRoutes
        and application.completed_app.CompiledRoutes
    ):
        for route in application.completed_app.CompiledRoutes:
            if (
                route.ApiRouteSpec
                and route.ApiRouteSpec.DatabaseSchema
                and route.ApiRouteSpec.DatabaseSchema.DatabaseTables
            ):
                for table in route.ApiRouteSpec.DatabaseSchema.DatabaseTables:
                    if table.name not in table_names:
                        tables.append(table)
                        table_names.add(table.name)

    prisma_file = """
// datasource db defines the database connection settings.
// It is configured for PostgreSQL and uses an environment variable for the connection URL.
// The 'extensions' feature enables the use of PostgreSQL-specific data types.
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
  extensions = [vector]
}

// generator db configures Prisma Client settings.
// It is set up to use Prisma Client Python with asyncio interface and specific features.
generator db {
  provider             = "prisma-client-py"
  interface            = "asyncio"
  recursive_type_depth = 5
  previewFeatures      = ["postgresqlExtensions"]
}

    """
    if not tables:
        return ""

    for table in tables:
        prisma_file += table.definition
        prisma_file += "\n\n"

    return prisma_file


def create_zip_file(application: Application) -> bytes:
    """
    Creates a zip file from the application
    Args:
        application (Application): The application to be zipped

    Returns:
        bytes: The zipped file
    """
    logger.info("Creating zip file")

    if not application.completed_app:
        raise ValueError("Application must have a completed app")
    if not application.completed_app.CompiledRoutes:
        raise ValueError("Application must have at least one compiled route")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = os.path.join(temp_dir, "project")
            os.makedirs(app_dir, exist_ok=True)

            readme_file_path = os.path.join(app_dir, "README.md")
            with open(readme_file_path, "w") as readme_file:
                readme_file.write("---\n")
                current_date = datetime.datetime.now()
                formatted_date = current_date.isoformat()
                readme_file.write(f"date: {formatted_date}\n")
                readme_file.write("author: codex\n")
                readme_file.write("---\n\n")
                readme_file.write(f"# {application.completed_app.name}\n\n")
                readme_file.write(application.completed_app.description)

            init_file_path = os.path.join(app_dir, "__init__.py")
            with open(init_file_path, "w") as init_file:
                init_file.write("")

            server_file_path = os.path.join(app_dir, "server.py")
            with open(server_file_path, "w") as server_file:
                server_file.write(application.server_code)

            for compiled_route in application.completed_app.CompiledRoutes:
                service_file_path = os.path.join(app_dir, compiled_route.fileName)
                with open(service_file_path, "w") as service_file:
                    service_file.write(compiled_route.compiledCode)

            pipreqs.init(
                {
                    "<path>": app_dir,
                    "--savepath": os.path.join(app_dir, "requirements.txt"),
                    "--print": False,
                    "--use-local": None,
                    "--force": True,
                    "--proxy": None,
                    "--pypi-server": None,
                    "--diff": None,
                    "--clean": None,
                    "--mode": "no-pin",
                }
            )

            requirements_file_path = os.path.join(app_dir, "requirements.txt")
            pipreq_pacakages = []
            with open(file=requirements_file_path, mode="r") as requirements_file:
                pipreq_pacakages = requirements_file.readlines()

            packages = ""
            if application.packages:
                packages = generate_requirements_txt(
                    application.packages, pipreq_pacakages
                )

            os.remove(requirements_file_path)

            with open(requirements_file_path, mode="w") as requirements_file:
                requirements_file.write(packages)

            prism_schema_file_path = os.path.join(app_dir, "schema.prisma")
            prisma_content = create_prisma_scheama_file(application)
            if prisma_content:
                with open(prism_schema_file_path, mode="w") as prisma_file:
                    prisma_file.write(prisma_content)

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
