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


async def create_sample_app(user_id: str, cloud_id: str, title: str, description: str):
    app = await create_app(
        user_id,
        ApplicationCreate(
            name=title,
            description=description,
        ),
    )

    ids = Identifiers(user_id=user_id, app_id=app.id, cloud_services_id=cloud_id)

    spec = await create_spec(
        ids,
        spec=ApplicationRequirements(
            name=title,
            context=description,
            api_routes=[
                APIRouteRequirement(
                    method="GET",
                    path="/",
                    function_name="main",
                    description="A page that renders " + description,
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
    title="",
    description="",
) -> list[str] | None:
    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})

    async def execute():
        app_id, spec = await create_sample_app(user_id, cloud_id, title, description)
        ids = Identifiers(user_id=user_id, app_id=app_id, cloud_services_id=cloud_id)
        func = await agent.develop_application(ids=ids, spec=spec, lang="nicegui")
        return await get_compiled_code(func.id) if func else None

    return await with_db_connection(execute)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_tictactoe():
    func = await generate_function(
        title="TicTacToe Game",
        description="A simple TicTacToe game",
    )
    assert func is not None

@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_tictactoe():
    func = await generate_function(
        title="TODO List",
        description="A TODO List application that support Add, Delete and Update operations",
    )
    assert func is not None
