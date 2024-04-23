from typing import Callable

import pytest
from prisma.enums import AccessLevel, HTTPVerb

from codex.api_model import ApplicationCreate
from codex.app import db_client
from codex.common.ai_model import AIChatClient
from codex.common.logging_config import setup_logging
from codex.common.model import ObjectFieldModel, ObjectTypeModel
from codex.common.test_const import Identifiers, user_id_1
from codex.database import create_app, get_app_by_id
from codex.develop import agent
from codex.develop.database import get_compiled_code
from codex.requirements.agent import APIRouteSpec, Module, SpecHolder
from codex.requirements.database import create_specification

is_connected = False
setup_logging()


async def create_sample_app(user_id: str, cloud_id: str, title: str, description: str):
    app_id = (
        await create_app(
            user_id,
            ApplicationCreate(
                name=title,
                description=description,
            ),
        )
    ).id

    app = await get_app_by_id(user_id, app_id)

    ids = Identifiers(user_id=user_id, app_id=app.id, cloud_services_id=cloud_id)

    spec_holder = SpecHolder(
        ids=ids,
        app=app,
        modules=[
            Module(
                name=title,
                description=description,
                api_routes=[
                    APIRouteSpec(
                        module_name="Main Function",
                        http_verb=HTTPVerb.POST,
                        function_name="main",
                        path="/",
                        description="A page that renders " + description,
                        access_level=AccessLevel.PUBLIC,
                        allowed_access_roles=[],
                        request_model=ObjectTypeModel(
                            name="request",
                            Fields=[
                                ObjectFieldModel(name="client", type="nicegui.Client"),
                            ],
                        ),
                        response_model=None,
                    )
                ],
            )
        ],
    )

    spec = await create_specification(spec_holder)

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
    if not AIChatClient._configured:
        AIChatClient.configure({})

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
async def test_todo_list():
    func = await generate_function(
        title="TODO List",
        description="A TODO List application that support Add, Delete and Update operations",
    )
    assert func is not None
