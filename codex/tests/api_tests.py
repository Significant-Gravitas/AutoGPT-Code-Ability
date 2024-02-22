import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

from codex import app
from codex.common.test_const import *


@pytest.fixture
def client():
    with TestClient(app.app) as c:
        yield c


API: str = "/api/v1"


def test_user_apis(client):
    # List Users
    response = client.get(f"{API}/user/")
    assert response.status_code == 200
    users = response.json()["users"]
    assert len(users) > 0
    user = next((u for u in users if u["id"] == user_id_1), None)
    assert user is not None

    # Get User
    response = client.get(f"{API}/user/{user['id']}")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == user_id_1

    # Get User by Discord ID
    response = client.get(f"{API}/discord/{user['discord_id']}")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == user_id_1


def test_apps_apis(client):
    # Create App
    response = client.post(f"{API}/user/{user_id_1}/apps/", json={"name": "Test App"})
    assert response.status_code == 200
    app = response.json()
    assert app["name"] == "Test App"
    assert app["userid"] == user_id_1

    # List Apps
    response = client.get(f"{API}/user/{user_id_1}/apps/")
    assert response.status_code == 200
    apps = response.json()["applications"]
    assert len(apps) > 0
    assert next((a for a in apps if a["id"] == app["id"]), None) is not None

    # Get App
    response = client.get(f"{API}/user/{user_id_1}/apps/{app['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == app["id"]

    # Delete App
    response = client.delete(f"{API}/user/{user_id_1}/apps/{app['id']}")
    assert response.status_code == 200
    response = client.get(f"{API}/user/{user_id_1}/apps/")
    apps = response.json()["applications"]
    assert next((a for a in apps if a["id"] == app["id"]), None) is None


def test_specs_and_deliverables_apis(client):
    # List Specs
    response = client.get(f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/")
    assert response.status_code == 200
    specs = response.json()["specs"]
    assert len(specs) > 0

    # Get Spec
    spec_id = specs[0]["id"]
    response = client.get(f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/{spec_id}")
    assert response.status_code == 200
    spec = response.json()
    assert spec["id"] == spec_id

    # List Deliverables
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/{spec_id}/deliverables/"
    )
    assert response.status_code == 200
    deliverables = response.json()["deliverables"]
    assert len(deliverables) >= 0

    ## Create (and Delete) is skipped for now, since it's taking too long to create a spec ##

    # Create Spec
    # response = client.post(f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/", json={"description": "Test Spec"})
    # assert response.status_code == 200
    # spec = response.json()
    # assert spec['description'] == "Test Spec"

    # Delete Spec
    # response = client.delete(f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/{spec['id']}")
    # assert response.status_code == 200
    # response = client.get(f"{API}/user/{user_id_1}/apps/{app_id_1}/specs/")
    # specs = response.json()['specs']
    # assert next((s for s in specs if s['id'] == spec['id']), None) is None


from prisma.models import APIRouteSpec

from codex.app import db_client
from codex.architect import agent
from codex.architect.model import FunctionDef


@pytest.mark.asyncio
async def test_recursive_create_code_graphs():
    await db_client.connect()

    entry_point_function = "start_game"
    goal = "Create a CLI TicTacToe game"

    # Find any api_route for now from the DB, we only use it for dummy data. Find all and get first
    api_route = await APIRouteSpec.prisma().find_first()
    func_def = FunctionDef(
        name=entry_point_function,
        doc_string="dummy",
        args="dummy",
        return_type="dummy",
        function_template="",
    )

    code_graph = await agent.recursive_create_code_graphs(
        ids=Identifiers(user_id=user_id_1, app_id=app_id_1, spec_id="123"),
        goal=goal,
        func_def=func_def,
        api_route=api_route,
    )
    assert code_graph is not None
