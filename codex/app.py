import logging

from fastapi import FastAPI
from prisma import Prisma

from codex.api import core_routes
from codex.architect.routes import delivery_router
from codex.deploy.routes import deployment_router
from codex.developer.routes import developer_routes
from codex.requirements.routes import spec_router

logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)

app = FastAPI(
    title="Codex",
    description=(
        "Codex is a platform for creating, deploying, and managing web applications."
    ),
    summary="Codex API",
    version="0.1",
)


app.include_router(core_routes, prefix="/api/v1")
app.include_router(spec_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(developer_routes, prefix="/api/v1")
app.include_router(deployment_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    await db_client.connect()


@app.on_event("shutdown")
async def shutdown():
    await db_client.disconnect()
