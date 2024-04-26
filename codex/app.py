import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from prisma import Prisma
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from codex.api import core_routes
from codex.deploy.routes import deployment_router
from codex.develop.routes import delivery_router
from codex.interview.routes import interview_router
from codex.middleware import RouterLoggingMiddleware
from codex.requirements.routes import spec_router

load_dotenv()
logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.disconnect()


sentry_sdk.init(
    dsn="https://0dc3905d347a9e4e81280f02deac234d@o4505260022104064.ingest.sentry.io/4506844882075648",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
    enable_tracing=True,
    environment=os.environ.get("RUN_ENV", default="CLOUD").lower(),
    integrations=[
        StarletteIntegration(transaction_style="url"),
        FastApiIntegration(transaction_style="url"),
        AsyncioIntegration(),
        AioHttpIntegration(),
    ],
)
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

app.add_middleware(RouterLoggingMiddleware)
