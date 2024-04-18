from typing import Callable

import pytest
from dotenv import load_dotenv

load_dotenv()

from codex.api_model import ApplicationCreate
from codex.app import db_client
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.model import ObjectFieldModel, ObjectTypeModel
from codex.common.test_const import Identifiers, user_id_1
from codex.database import create_app
from codex.develop import agent
from codex.develop.database import get_compiled_code
from codex.requirements.database import create_spec
from codex.requirements.model import (
    AccessLevel,
    APIRouteRequirement,
    ApplicationRequirements,
)

load_dotenv()
is_connected = False
setup_logging()


async def create_sample_app(user_id: str, cloud_id: str):
    app = await create_app(
        user_id,
        ApplicationCreate(
            name="TicTacToe Game",
            description="A TicTacToe Game.",
        ),
    )

    ids = Identifiers(user_id=user_id, app_id=app.id, cloud_services_id=cloud_id)

    spec = await create_spec(
        ids,
        spec=ApplicationRequirements(
            name="TicTacToe Game",
            context="A TicTacToe Game.",
            api_routes=[
                APIRouteRequirement(
                    method="GET",
                    path="/",
                    function_name="main",
                    description="A page that shows a TicTacToe Game board.",
                    access_level=AccessLevel.PUBLIC,
                    request_model=ObjectTypeModel(
                        name="request",
                        Fields=[
                            ObjectFieldModel(name="client", type="nicegui.Client"),
                        ],
                    ),
                    response_model=None,
                    database_schema=None,
                ),
            ],
        ),
    )

    return app.id, spec


async def with_db_connection(func: Callable):
    global is_connected
    if not is_connected:
        await db_client.connect()
        is_connected = True

    result = await func()

    if is_connected:
        await db_client.disconnect()
        is_connected = False

    return result


async def generate_function(
    user_id=user_id_1,
    cloud_id="",
) -> list[str] | None:
    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})

    async def execute():
        app_id, spec = await create_sample_app(user_id, cloud_id)
        ids = Identifiers(user_id=user_id, app_id=app_id, cloud_services_id=cloud_id)
        func = await agent.develop_application(ids=ids, spec=spec, lang="nicegui")
        return await get_compiled_code(func.id) if func else None

    return await with_db_connection(execute)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_simple_function():
    func = await generate_function()
    assert func is not None
