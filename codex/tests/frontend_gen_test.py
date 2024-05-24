import logging
from typing import Callable

import pytest
from prisma.enums import AccessLevel, HTTPVerb

from codex.api_model import ApplicationCreate, ObjectFieldModel, ObjectTypeModel
from codex.app import db_client
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.test_const import Identifiers, user_id_1
from codex.database import create_app, get_app_by_id
from codex.deploy import agent as deploy_agent
from codex.develop import agent
from codex.develop.database import get_compiled_code, get_deliverable
from codex.requirements.agent import APIRouteSpec, Module, SpecHolder
from codex.requirements.database import create_specification, get_specification

is_connected = False
setup_logging()
logger = logging.getLogger(__name__)


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
                    ),
                ],
                interactions="",
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
@pytest.mark.skip  # This is a manual run for testing
async def test_tictactoe():
    func = await generate_function(
        title="TicTacToe Game",
        description="A simple TicTacToe game",
    )
    assert func is not None


@pytest.mark.asyncio
@pytest.mark.integration_test
@pytest.mark.skip  # This is a manual run for testing
async def test_todo_list():
    func = await generate_function(
        title="TODO List",
        description="A TODO List application that support Add, Delete and Update operations",
    )
    assert func is not None


@pytest.mark.skip  # This is a manual run for testing
async def generate_user_interface(completed_app_id: str):
    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})

    completed_app = await with_db_connection(lambda: get_deliverable(completed_app_id))

    ids = Identifiers(
        user_id=completed_app.userId,
        app_id=completed_app.applicationId,
        completed_app_id=completed_app.id,
    )

    async def develop_app() -> object:
        assert ids.completed_app_id
        app = await get_deliverable(ids.completed_app_id)
        if app.companionCompletedAppId is not None:
            logger.warn("Skip generating the UI, the provided app is already a UI app")
            return app

        completed_app = await agent.develop_user_interface(ids)
        assert completed_app
        return completed_app

    app = await with_db_connection(develop_app)
    assert app is not None

    ids = Identifiers(
        user_id=app.userId,
        app_id=app.applicationId,
        completed_app_id=app.id,
    )

    async def deploy_app() -> object:
        assert ids.completed_app_id
        assert ids.user_id
        assert ids.app_id
        completed_app = await get_deliverable(ids.completed_app_id)

        assert completed_app
        assert completed_app.specificationId
        spec = await get_specification(
            ids.user_id, ids.app_id, completed_app.specificationId
        )

        deployment = await deploy_agent.create_local_deployment(
            ids, completed_app, spec
        )
        assert deployment
        return deployment

    deployment = await with_db_connection(deploy_app)
    assert deployment is not None
    logger.info("Deployment completed, ID: " + deployment.id)
    return deployment
