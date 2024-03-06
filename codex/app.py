import logging

from fastapi import FastAPI
from prisma import Prisma
from contextlib import asynccontextmanager

from codex.api import core_routes
from codex.deploy.routes import deployment_router
from codex.develop.routes import delivery_router
from codex.interview.routes import interview_router
from codex.requirements.routes import spec_router

logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.disconnect()


app = FastAPI(
    title="Codex",
    description=(
        "Codex is a platform for creating, deploying, and managing web applications."
    ),
    summary="Codex API",
    version="0.1",
    lifespan=lifespan,
)


app.include_router(core_routes, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(spec_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(deployment_router, prefix="/api/v1")
