import logging
import os
import tempfile
from contextlib import asynccontextmanager
from enum import Enum

import coloredlogs
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine  # type: ignore
from starlette.background import BackgroundTask

from .agent import run

DATABASE_URL = "postgresql://agpt_live:bnfaHGGSDF134345@0.0.0.0:5432/agpt_product"
engine = create_engine(DATABASE_URL)


# Enum for Runner
class RunnerEnum(str, Enum):
    server = "Server"
    cli = "CLI"


# Request model
class CodeRequest(BaseModel):
    description: str
    user_id: int


# Basic authentication
security = HTTPBasic()

# Hardcoded valid credentials
valid_credentials = {
    "admin": "asd453jnsdof9384rjnsdf",
    "agpt": "asdfjkl1234",
}


# Authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if (
        credentials.username in valid_credentials
        and valid_credentials[credentials.username] == credentials.password
    ):
        return credentials.username
    raise HTTPException(status_code=401, detail="Unauthorized")


# FastAPI app
app = FastAPI()


def setup_logging():
    # Define the log format
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    # Set up basic configuration with standard output
    logging.basicConfig(level=logging.INFO, format=log_format)
    coloredlogs.install(level="INFO", fmt=log_format)

    # Create a file handler for error messages
    file_handler = logging.FileHandler("codex_logs.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Create a file handler for error messages
    err_file_handler = logging.FileHandler("error_logs.log")
    err_file_handler.setLevel(logging.ERROR)
    err_file_handler.setFormatter(logging.Formatter(log_format))

    # Add the file handler to the root logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(err_file_handler)


setup_logging()
logger = logging.getLogger(__name__)


@app.post("/code")
def handle_code_request(request: CodeRequest, user: str = Depends(authenticate)):
    logger.info(f"Received code request from user: {user}")
    try:
        zip_bytes = run(request.description, engine)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
    # Create a temporary file
    temp_file, temp_file_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_file)

    # Write zip_bytes to the temporary file
    with open(temp_file_path, "wb") as file:
        file.write(zip_bytes)

    logger.info("Returning zip file response")
    return FileResponse(
        temp_file_path,
        media_type="application/zip",
        filename="code_output.zip",
        background=BackgroundTask(lambda: os.unlink(temp_file_path)),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    SQLModel.metadata.create_all(engine)
    yield
