# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster as codex_base

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y build-essential curl ffmpeg git netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
ENV POETRY_VERSION=1.1.8 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH"
RUN pip3 install poetry

# Copy only requirements to cache them in Docker layer
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/

# Copy entrypoint script and set permissions
COPY scripts/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

RUN mkdir /app/codex
RUN touch /app/codex/__init__.py
RUN touch /app/README.md

# Project initialization:
RUN poetry install --no-interaction --no-ansi

FROM codex_base as codex_db
# Caching prisma generate step
COPY schema.prisma /app/

RUN prisma generate

FROM codex_db as codex
# Fast build of codex - only needs to update the python code
COPY . /app

# Set a default value (this can be overridden)
ENV PORT=8000

# Just declare the variable, the value will be set when running the container
ENV OPENAI_API_KEY=""

## This will be the command to run the FastAPI server using uvicorn
#CMD ./run serve

# Specify the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]