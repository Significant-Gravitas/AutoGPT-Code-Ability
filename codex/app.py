import logging
import os
import tempfile
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlmodel import SQLModel, create_engine  # type: ignore
from starlette.background import BackgroundTask

from .agent import run
from .model import *

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/code")
def handle_code_request(request: CodeRequest, user: str = Depends(authenticate)):
    logger.info(f"Received code request from user: {user}")
    zip_bytes = run(request.description, engine)

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
