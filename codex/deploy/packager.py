import logging
import os
import random
import tempfile
import zipfile
from datetime import datetime
from typing import List

from pipreqs import pipreqs
from prisma.models import DatabaseTable, Package

from codex.deploy.model import Application

logger = logging.getLogger(__name__)


DOCKERFILE = """
# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster as autogpt_project

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y build-essential curl \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt /app
RUN pip install -r requirements.txt

# Generate Prisma client
RUN prisma generate

# Add application source
COPY project/ /app/project/

# Set a default port (this can be overridden)
ENV PORT=8000

# This will be the command to run the FastAPI server using uvicorn
CMD uvicorn project.server:app --port $PORT
"""


def generate_requirements_txt(
    packages: List[Package], pipreq_pacakages: List[str]
) -> str:
    requirements = set()

    for package in packages:
        requirements.add(package.packageName.replace("\n", "").strip())

    for package in pipreq_pacakages:
        requirements.add(package.replace("\n", "").strip())

    return "\n".join(sorted(requirements))


def generate_dotenv_example_file(application: Application) -> str:
    """
    Generates a .env.example file from the application
    Args:
        application (Application): The application to be used to generate the .env.example file

    Returns:
        str: The .env.example file
    """
    logger.info("Generating .env.example file")

    if not application.completed_app:
        raise ValueError("Application must have a completed app")
    if not application.completed_app.CompiledRoutes:
        raise ValueError("Application must have at least one compiled route")

    # Generate a random password
    random_password = "".join(
        random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for i in range(20)
    )
    # normalized app name. keeping only a-z and _
    db_name: str = (
        application.completed_app.name.lower().replace(" ", "_").replace("-", "_")
    )
    # regex to keep only a-z and _
    db_name = "".join([c if c.isalpha() else "" for c in db_name])
    env_example = """
# Example .env file
# Copy this file to .env and fill in the values for the environment variables
# The .env file should not be committed to version control
DB_USER="codexrulesman"
DB_PASS="{random_password}"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="{db_name}"
DATABASE_URL="postgresql://${{DB_USER}}:${{DB_PASS}}@${{DB_HOST}}:${{DB_PORT}}/${{DB_NAME}}"
""".lstrip()
    env_example = env_example.format(random_password=random_password, db_name=db_name)

    # env_example = ""
    # for compiled_route in application.completed_app.CompiledRoutes:
    #     if compiled_route.ApiRouteSpec and compiled_route.ApiRouteSpec.envVars:
    #         for env_var in compiled_route.ApiRouteSpec.envVars:
    #             env_example += f"{env_var.name}=\n"

    return env_example


def generate_gitignore_file() -> str:
    """
    Generates a .gitignore file
    Returns:
        str: The .gitignore file
    """
    return """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Translations
*.mo
*.pot

# FastAPI
__pycache__/

# Environment variables
.env
.env.(local|development|production|test|staging|qa)
.env*
!.env.example
""".lstrip()


def generate_docker_compose_file(application: Application) -> str:
    """
    Generates a docker-compose.yml file from the application
    Args:
        application (Application): The application to be used to generate the docker-compose.yml file

    Returns:
        str: The docker-compose.yml file
    """
    logger.info("Generating docker-compose.yml file")

    if not application.completed_app:
        raise ValueError("Application must have a completed app")
    if not application.completed_app.CompiledRoutes:
        raise ValueError("Application must have at least one compiled route")

    docker_compose = """
version: '3.8'
services:
    db:
        image: ankane/pgvector:latest
        environment:
            POSTGRES_USER: ${DB_USER}
            POSTGRES_PASSWORD: ${DB_PASS}
            POSTGRES_DB: ${DB_NAME}
        ports:
        - "5432:5432"
    app:
        build:
            context: .
            dockerfile: Dockerfile
        environment:
            DATABASE_URL: ${DATABASE_URL}
            PORT: 8080
        ports:
        - "8080:8080"
""".lstrip()

    return docker_compose


async def create_prisma_schema_file(application: Application) -> str:
    tables = []
    db_schema_id = None

    if not (
        application.completed_app.CompiledRoutes
        and application.completed_app.CompiledRoutes
    ):
        raise ValueError("Application must have at least one compiled route")

    for route in application.completed_app.CompiledRoutes:
        if route.ApiRouteSpec and route.ApiRouteSpec.DatabaseSchema:
            db_schema_id = route.ApiRouteSpec.DatabaseSchema.id
            # the same schema is used for all routes
            break

    if not db_schema_id:
        logger.warning("No database schema found")
        return ""

    tables: List[DatabaseTable] = await DatabaseTable.prisma().find_many(
        where={"databaseSchemaId": db_schema_id}
    )

    prisma_file = """
// datasource db defines the database connection settings.
// It is configured for PostgreSQL and uses an environment variable for the connection URL.
// The 'extensions' feature enables the use of PostgreSQL-specific data types.
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
}

// generator db configures Prisma Client settings.
// It is set up to use Prisma Client Python with asyncio interface and specific features.
generator db {
  provider             = "prisma-client-py"
  interface            = "asyncio"
  recursive_type_depth = 5
  previewFeatures      = ["postgresqlExtensions"]
}

""".lstrip()
    if not tables:
        return ""

    for table in tables:
        prisma_file += table.definition
        prisma_file += "\n\n"

    return prisma_file


async def create_zip_file(application: Application) -> bytes:
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
        with tempfile.TemporaryDirectory() as package_dir:
            app_dir = os.path.join(package_dir, "project")
            os.makedirs(app_dir, exist_ok=True)

            # Make a readme file
            readme_file_path = os.path.join(package_dir, "README.md")
            with open(readme_file_path, "w") as readme_file:
                readme_file.write(generate_readme(application))

            dockerfile_path = os.path.join(package_dir, "Dockerfile")
            with open(dockerfile_path, "w") as dockerfile:
                dockerfile.write(DOCKERFILE)

            # Make a __init__.py file
            init_file_path = os.path.join(app_dir, "__init__.py")
            with open(init_file_path, "w") as init_file:
                init_file.write("")

            # Make a server.py file
            server_file_path = os.path.join(app_dir, "server.py")
            with open(server_file_path, "w") as server_file:
                server_file.write(application.server_code)

            # Make all the service files
            for compiled_route in application.completed_app.CompiledRoutes:
                service_file_path = os.path.join(app_dir, compiled_route.fileName)
                with open(service_file_path, "w") as service_file:
                    service_file.write(compiled_route.compiledCode)

            # Make a requirements file
            pipreqs.init(
                {
                    "<path>": package_dir,
                    "--savepath": os.path.join(package_dir, "requirements.txt"),
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

            requirements_file_path = os.path.join(package_dir, "requirements.txt")
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

            # Make a prisma schema file
            prism_schema_file_path = os.path.join(package_dir, "schema.prisma")
            prisma_content = await create_prisma_schema_file(application)
            if prisma_content:
                with open(prism_schema_file_path, mode="w") as prisma_file:
                    prisma_file.write(prisma_content)

            # Make a .env.example file
            dotenv_example_file_path = os.path.join(package_dir, ".env.example")
            dotenv_example = generate_dotenv_example_file(application)
            with open(dotenv_example_file_path, mode="w") as dotenv_example_file:
                dotenv_example_file.write(dotenv_example)

            # Also create .env for convenience
            dotenv_file_path = os.path.join(package_dir, ".env")
            with open(dotenv_file_path, mode="w") as dotenv_file:
                dotenv_file.write(dotenv_example)

            # Make a .gitignore file
            gitignore_file_path = os.path.join(package_dir, ".gitignore")
            gitignore = generate_gitignore_file()
            with open(gitignore_file_path, mode="w") as gitignore_file:
                gitignore_file.write(gitignore)

            # Make a docker-compose.yml file
            docker_compose_file_path = os.path.join(package_dir, "docker-compose.yml")
            docker_compose = generate_docker_compose_file(application)
            with open(docker_compose_file_path, mode="w") as docker_compose_file:
                docker_compose_file.write(docker_compose)

            logger.info("Created server code")
            # Create a zip file of the directory
            zip_file_path = os.path.join(app_dir, "server.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        if file == "server.zip":
                            continue
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, package_dir))

            logger.info("Created zip file")
            # Read and return the bytes of the zip file
            with open(zip_file_path, "rb") as zipf:
                zip_bytes = zipf.read()

            return zip_bytes
    except Exception as e:
        logger.exception(e)
        raise e


def generate_readme(application: Application) -> str:
    """Generates a README for the application

    Params:
        application (Application): The application for which to generate a README

    Returns:
        str: The README content
    """
    content: str = ""

    # Header
    # App name + description
    # Instructions to run the application
    content += f"""
---
date: {datetime.now().isoformat()}
author: AutoGPT
---

# {application.completed_app.name}

{application.completed_app.description}

## What you'll need to run this
* An unzipper (usually shipped with your OS)
* A text editor
* A terminal
* Docker
  > Docker is only needed to run a Postgres database. If you want to connect to your own
  > Postgres instance, you may not have to follow the steps below to the letter.


## How to run '{application.completed_app.name}'

1. Unpack the ZIP file containing this package

2. Create a copy of `.env.example` named `.env`. Adjust the values in it as you see fit.

3. Open a terminal in the folder containing this README and run the following commands:

    1. `pip install -r requirements.txt` - install dependencies for the app

    2. `docker-compose up -d` - start the postgres database

    3. `prisma generate` - generate the database client for the app

    4. `prisma db push` - set up the database schema, creating the necessary tables etc.

4. Run `uvicorn project.server:app --reload` to start the app
""".lstrip()

    return content
