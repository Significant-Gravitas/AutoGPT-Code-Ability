import logging
import os
import random
import tempfile
import zipfile
import requests
from datetime import datetime
from typing import List

from git import GitCommandError
from git.repo import Repo
from prisma.models import DatabaseTable

from codex.common.constants import PRISMA_FILE_HEADER
from codex.common.exec_external_tool import execute_command
from codex.deploy.model import Application

logger = logging.getLogger(__name__)

PROJECT_AUTHOR = "AutoGPT <info@agpt.co>"

DOCKERFILE = """
# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y build-essential curl \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install and configure Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_PATH="/venv"
ENV POETRY_VIRTUALENVS_IN_PROJECT=0
ENV POETRY_NO_INTERACTION=1
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-cache --no-root

# Generate Prisma client
COPY schema.prisma /app/
RUN poetry run prisma generate

# Copy project code
COPY project/ /app/project/

# Serve the application on port 8000
CMD poetry run uvicorn project.server:app --host 0.0.0.0 --port 8000
EXPOSE 8000
""".lstrip()


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
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
            interval: 10s
            timeout: 5s
            retries: 5
    app:
        build:
            context: .
            dockerfile: Dockerfile
        environment:
            # Override DATABASE_URL from .env with host and port (db:5432) of DB service
            DATABASE_URL: "postgresql://${DB_USER}:${DB_PASS}@db:5432/${DB_NAME}"
        ports:
        - "${PORT:-8080}:8000"
        depends_on:
            db:
                condition: service_healthy
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

    prisma_file = f"{PRISMA_FILE_HEADER}".lstrip()
    if not tables:
        return ""

    for table in tables:
        prisma_file += table.definition
        prisma_file += "\n\n"

    return prisma_file


def create_github_repo(repo_name: str) -> str:
    """
    Creates a new GitHub repository under Significant-Gravitas.

    Args:
        repo_name (str): The name of the repository to create.

    Returns:
        str: The HTTPS URL of the newly created repository.

    Raises:
        Exception: If the repository creation fails.
    """

    GIT_TOKEN: str = os.environ.get("GIT_TOKEN")
    if not GIT_TOKEN:
        logger.error("GitHub token not found in environment variables.")
        return

    url = f"https://api.github.com/orgs/Significant-Gravitas/repos"
    headers = {
        "Authorization": f"token {GIT_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"name": repo_name, "private": False}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        repo_url = response.json()["html_url"]
        logger.info(f"Repository created at {repo_url}")
        authenticated_url = repo_url.replace("https://", f"https://{GIT_TOKEN}@")
        return authenticated_url
    else:
        raise Exception(f"Failed to create repository: {response.text}")


def git_init(app_dir: str):
    """
    Initializes a Git repository in the specified directory and pushes all files.

    Args:
        app_dir (str): The directory path where the Git repository should be initialized.

    Raises:
        GitCommandError: if any of the Git operations fails.
    """
    GIT_USER_NAME: str = os.environ.get("GIT_USER_NAME", default="AutoGPT")
    GIT_USER_EMAIL: str = os.environ.get("GIT_USER_EMAIL", default="code@agpt.co")

    try:
        # Initialize Git repository
        repo = Repo.init(app_dir)

        # Configure Git user for the current session
        repo.git.set_persistent_git_options(
            c=[
                f"user.name={GIT_USER_NAME}",
                f"user.email={GIT_USER_EMAIL}",
                "commit.gpgsign=false",
            ]
        )

        repo.git.add(".")
        repo.index.commit("Initial commit")

        logger.info("Git repository initialized and all files committed")

        remote_url = create_github_repo(app_dir)
        origin = repo.create_remote("origin", remote_url)
        origin.push("master")
        logger.info(f"Code successfully pushed to repo")

    except GitCommandError as e:
        logger.exception("Failed to initialize Git repository or commit files:", e)
        raise e


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

            # Create pyproject.toml and poetry.lock
            logger.info("Creating pyproject.toml")
            await create_pyproject(application=application, package_dir=package_dir)
            logger.info("Creating poetry.lock")
            await poetry_lock(package_dir)

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

            # Initialize a Git repository and commit everything
            git_init(app_dir=package_dir)

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
author: {PROJECT_AUTHOR}
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

2. Adjust the values in `.env` as you see fit.

3. Open a terminal in the folder containing this README and run the following commands:

    1. `poetry install` - install dependencies for the app

    2. `docker-compose up -d` - start the postgres database

    3. `prisma generate` - generate the database client for the app

    4. `prisma db push` - set up the database schema, creating the necessary tables etc.

4. Run `uvicorn project.server:app --reload` to start the app
""".lstrip()

    return content


async def create_pyproject(application: Application, package_dir: str) -> None:
    """Create a pyproject.toml file for `application` in `package_dir`"""
    app_name_slug = application.name.lower().replace(" ", "-")
    app_description = application.description.split("\n", 1)[0]
    dependency_args = [
        f"--dependency={p.packageName}{f':^{p.version}' if p.version else '=*'}"
        for p in sorted(application.packages, key=lambda p: p.packageName)
    ]
    await execute_command(
        command=[
            "poetry",
            "init",
            f"--name={app_name_slug}",
            f"--description={app_description}",
            f"--author={PROJECT_AUTHOR}",
            "--python=>=3.11",
            *dependency_args,
            "--no-interaction",
        ],
        cwd=package_dir,
    )


async def poetry_lock(package_dir: str) -> None:
    """Runs `poetry lock` in the given `package_dir`"""
    if not os.path.exists(f"{package_dir}/pyproject.toml"):
        raise FileNotFoundError(
            f"Can not generate lockfile in {package_dir} without pyproject.toml"
        )
    await execute_command(
        command=["poetry", "lock"],
        cwd=package_dir,
    )
