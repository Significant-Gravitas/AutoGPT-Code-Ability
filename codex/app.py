import logging
import os
import zipfile
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine  # type: ignore

from .agent import run

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)


# Enum for Runner
class RunnerEnum(str, Enum):
    server = "Server"
    cli = "CLI"


# Request model
class CodeRequest(BaseModel):
    description: str
    user_id: int
    runner: RunnerEnum


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


# Function to create a dummy zip file
def create_dummy_zip():
    zip_file_path = "dummy_file.zip"
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        # Add a dummy file to the zip
        dummy_file_name = "dummy.txt"
        with open(dummy_file_name, "w") as file:
            file.write("This is a dummy file.")

        zipf.write(dummy_file_name)

        # Cleanup the dummy file
        os.remove(dummy_file_name)

    return zip_file_path


@app.post("/code")
def handle_code_request(request: CodeRequest, user: str = Depends(authenticate)):
    logger.info(f"Received code request from user: {user}")
    code = run(request.description)
    # Create a dummy zip file
    zip_file_path = create_dummy_zip()

    logger.info("Returning zip file response")
    return FileResponse(
        zip_file_path, media_type="application/zip", filename="dummy_file.zip"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    SQLModel.metadata.create_all(engine)
    yield
