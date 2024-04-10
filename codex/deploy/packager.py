import logging
import os
import random
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List

import aiohttp
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


def generate_actions_workflow(application: Application) -> str:
    """
    Generates a deploy.yml file for the application
    Args:
        application (Application): The application to be used to generate the deploy.yml file

    Returns:
        str: The deploy.yml file
    """
    logger.info("Generating deploy.yml file")

    if not application.completed_app:
        raise ValueError("Application must have a completed app")
    if not application.completed_app.CompiledRoutes:
        raise ValueError("Application must have at least one compiled route")

    deploy_file = """
name: cloudrun-deploy
#on:
#  push:
#    branches:
#      - master
on: workflow_dispatch
jobs:
  setup-build-publish-deploy:
    name: Setup, Build, Publish, and Deploy
    runs-on: ubuntu-latest
    steps:
    - name: Checkout
      uses: actions/checkout@master

      # Set up auth service account with Credentials
    - name: Set up auth service account
      uses: google-github-actions/auth@v2
      with:
        credentials_json: '${{ secrets.GCP_CREDENTIALS }}'

    # Setup gcloud CLI
    - name: Set up gcloud
      uses: google-github-actions/setup-gcloud@v2
      with:
        service_account_email: ${{ secrets.GCP_EMAIL }}
        service_account_key: ${{ secrets.GCP_CREDENTIALS }}
        export_default_credentials: true
    
    # Configure Docker with Credentials
    - name: Configure Docker
      run: |
        gcloud auth configure-docker
      
    # Build the Docker image
    - name: Build & Publish
      run: |
        gcloud config set project ${{ secrets.GCP_PROJECT }}
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT }}/${{ secrets.GCP_APPLICATION }}
        gcloud config set run/region us-central1
        
    - name: Deploy
      run: |
        gcloud run deploy ${{ secrets.GCP_APPLICATION }} --image gcr.io/${{ secrets.GCP_PROJECT }}/${{ secrets.GCP_APPLICATION }} --platform managed --allow-unauthenticated --memory 512M
""".lstrip()

    return deploy_file


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


async def create_github_repo(application: Application) -> str:
    """
    Creates a new GitHub repository under agpt-coder.

    Args:
        application (Application): The application to be used to create the github repo

    Returns:
        str: The HTTPS URL of the newly created repository.

    Raises:
        Exception: If the repository creation fails.
    """

    GIT_TOKEN: str | None = os.environ.get("GIT_TOKEN")
    if not GIT_TOKEN:
        raise EnvironmentError("GitHub token not found in environment variables.")

    url = "https://api.github.com/orgs/agpt-coder/repos"
    headers = {
        "Authorization": f"token {GIT_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    # App name plus a random slug word trio to avoid conflicts
    repo_name = application.name.lower().replace(" ", "-") + str(uuid.uuid4())

    # We should condition the repo status on the app development environment
    data = {"name": repo_name, "private": True}
    # Create the repository
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, json=data) as response:
            if response.status == 201:
                repo_url = (await response.json())["html_url"]
                logger.info(f"Repository created at {repo_url}")
                authenticated_url = (
                    repo_url.replace("https://", f"https://{GIT_TOKEN}:x-oauth-basic@")
                    + ".git"
                )
                return authenticated_url
            else:
                raise Exception(f"Failed to create repository: {response.text}")


def git_init(app_dir: Path) -> Repo:
    """
    Initializes a Git repository in the specified directory and commits all files.

    Args:
        app_dir (Path): The directory path where the Git repository should be initialized.

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
        return repo

    except GitCommandError as e:
        logger.exception("Failed to initialize Git repository or commit files:", e)
        raise e


def push_to_remote(repo: Repo, remote_name: str, remote_url: str):
    """
    Pushes the local branch to the remote repository.
    """
    try:
        origin = repo.create_remote(remote_name, remote_url)
        origin.push(refspec="main:main")
        logger.info("Code successfully pushed.")
    except GitCommandError as e:
        logger.error(f"Failed to push code: {e}")
        raise


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
            package_dir = Path(package_dir)
            app_dir = package_dir / "project"
            app_dir.mkdir(parents=True, exist_ok=True)

            # Make a readme file
            readme_file = package_dir / "README.md"
            readme_file.write_text(generate_readme(application))

            dockerfile = package_dir / "Dockerfile"
            dockerfile.write_text(DOCKERFILE)

            # Make a __init__.py file
            init_file = app_dir / "__init__.py"
            init_file.touch()

            # Make a server.py file
            server_file = app_dir / "server.py"
            server_file.write_text(application.server_code)

            # Make all the service files
            for compiled_route in application.completed_app.CompiledRoutes:
                service_file = app_dir / compiled_route.fileName
                service_file.write_text(compiled_route.compiledCode)

            # Create pyproject.toml and poetry.lock
            logger.info("Creating pyproject.toml")
            await create_pyproject(application=application, package_dir=package_dir)
            logger.info("Creating poetry.lock")
            await poetry_lock(package_dir)

            # Make a prisma schema file
            prisma_schema_file = package_dir / "schema.prisma"
            prisma_schema = await create_prisma_schema_file(application)
            if prisma_schema:
                prisma_schema_file.write_text(prisma_schema)

            # Make a .env.example file
            dotenv_example_file = package_dir / ".env.example"
            dotenv_example = generate_dotenv_example_file(application)
            dotenv_example_file.write_text(dotenv_example)

            # Also create .env for convenience
            dotenv_file = package_dir / ".env"
            dotenv_file.write_text(dotenv_example)

            # Make a .gitignore file
            gitignore_file = package_dir / ".gitignore"
            gitignore = generate_gitignore_file()
            gitignore_file.write_text(gitignore)

            # Make a docker-compose.yml file
            docker_compose_file = package_dir / "docker-compose.yml"
            docker_compose = generate_docker_compose_file(application)
            docker_compose_file.write_text(docker_compose)

            # Make a GitHub actions deploy file
            github_workflows_directory = package_dir / ".github" / "workflows"
            github_workflows_directory.mkdir(parents=True, exist_ok=True)

            github_deploy_workflow_path = github_workflows_directory / "deploy.yml"
            github_deploy_workflow_path.write_text(
                generate_actions_workflow(application)
            )

            # Initialize a Git repository and commit everything
            repo = git_init(app_dir=package_dir)

            remote_url = await create_github_repo(application)
            push_to_remote(repo, "origin", remote_url)

            logger.info("Code successfully pushed to repo")

            logger.info("Created server code")

            # Create a zip file of the directory
            zip_file_path = app_dir / "server.zip"
            with zipfile.ZipFile(zip_file_path, "w") as zipf:
                for file in package_dir.rglob("*"):
                    if file.is_file() and file.name != "server.zip":
                        zipf.write(file, file.relative_to(package_dir))
            logger.info("Created zip file")

            # Read and return the bytes of the zip file
            return zip_file_path.read_bytes()
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

## How to deploy on your own GCP account
1. Set up a GCP account
2. Create secrets: GCP_EMAIL (service account email), GCP_CREDENTIALS (service account key), GCP_PROJECT, GCP_APPLICATION (app name)
3. Ensure service account has following permissions: 
    Cloud Build Editor
    Cloud Build Service Account
    Cloud Run Developer
    Service Account User
    Service Usage Consumer
    Storage Object Viewer
4. Remove on: workflow, uncomment on: push (lines 2-6)
5. Push to master branch to trigger workflow
""".lstrip()

    return content


async def create_pyproject(application: Application, package_dir: Path) -> None:
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


async def poetry_lock(package_dir: Path) -> None:
    """Runs `poetry lock` in the given `package_dir`"""
    if not (package_dir / "pyproject.toml").exists():
        raise FileNotFoundError(
            f"Can not generate lockfile in {package_dir} without pyproject.toml"
        )
    await execute_command(
        command=["poetry", "lock"],
        cwd=package_dir,
    )
