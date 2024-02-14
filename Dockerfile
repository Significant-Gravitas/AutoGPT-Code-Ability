# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster as codgegenbase

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y build-essential curl ffmpeg \
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

RUN mkdir /app/proxy
RUN touch /app/proxy/__init__.py
RUN touch /app/README.md

FROM codgegenbase as codegendependencies

# Project initialization:
RUN poetry install --no-interaction --no-ansi


FROM codegendependencies as codegen
COPY . /app
# Set a default value (this can be overridden)
ENV PORT=8000

# Just declare the variable, the value will be set when running the container
ENV OPENAI_API_KEY=""

RUN prisma generate

# This will be the command to run the FastAPI server using uvicorn
CMD ./run serve
