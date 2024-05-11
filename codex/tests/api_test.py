import asyncio

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from codex import app
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.test_const import user_id_1

load_dotenv()
setup_logging()


app_id = ""
spec = None


@pytest.fixture
def client():
    from codex.tests.gen_test import create_sample_app, with_db_connection

    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})

    async def create_app():
        return await create_sample_app(user_id_1, "Test App")

    async def init():
        return await with_db_connection(create_app)

    global app_id, spec
    app_id, spec = asyncio.get_event_loop().run_until_complete(init())

    with TestClient(app.app) as c:
        yield c


API: str = "/api/v1"


@pytest.mark.integration_test
def test_user_apis(client):
    # List Users
    response = client.get(
        f"{API}/user/",
    )
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

    # Create / Get User by Discord and Cloud Services ID
    response = client.post(
        f"{API}/user",
        params={
            "discord_id": user["discord_id"],
            "cloud_services_id": user["cloud_services_id"],
        },
    )
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == user_id_1


@pytest.mark.integration_test
def test_apps_apis(client):
    # Create App
    response = client.post(f"{API}/user/{user_id_1}/apps/", json={"name": "Test App"})
    assert response.status_code == 200
    app = response.json()
    assert app["name"] == "Test App"
    assert app["userid"] == user_id_1

    # List Apps
    response = client.get(f"{API}/user/{user_id_1}/apps?page=1&page_size=100")
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


@pytest.mark.integration_test
@pytest.mark.skip
def test_interview_apis(client):
    # Create Interview
    response = client.post(
        f"{API}/user/{user_id_1}/apps/{app_id}/interview/",
        json={"task": "Test Task", "name": "Test Interview"},
    )
    assert response.status_code == 200
    interview = response.json()
    assert interview["id"]
    assert isinstance(interview["phase_completed"], bool)
    assert isinstance(interview["id"], str)

    interview_id = interview["id"]

    # Next Step Interview
    response = client.post(
        f"{API}/user/{user_id_1}/apps/{app_id}/interview/{interview_id}/next",
        json=[],
    )
    assert response.status_code == 200
    interview = response.json()
    assert interview["id"] == interview_id
    assert isinstance(interview["phase_completed"], bool)
    assert isinstance(interview["id"], str)

    # Delete Interview
    response = client.delete(
        f"{API}/user/{user_id_1}/apps/{app_id}/interview/{interview['id']}"
    )
    assert response.status_code == 200


@pytest.mark.integration_test
def test_specs_apis(client):
    # List Specs
    response = client.get(f"{API}/user/{user_id_1}/apps/{app_id}/specs/")
    assert response.status_code == 200
    specs = response.json()["specs"]
    assert len(specs) > 0

    # Get Spec
    spec_id = specs[0]["id"]
    response = client.get(f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}")
    assert response.status_code == 200
    spec = response.json()
    assert spec["id"] == spec_id

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


@pytest.mark.integration_test
@pytest.mark.skip
def test_deliverables_and_deployments_apis(client):
    ###### Deliverables ######
    spec_id = client.get(f"{API}/user/{user_id_1}/apps/{app_id}/specs/").json()[
        "specs"
    ][0]["id"]

    # Create Deliverable
    response = client.post(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/"
    )
    assert response.status_code == 200
    deliverable = response.json()
    assert deliverable["id"] is not None
    assert deliverable["name"] is not None

    # List Deliverables
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/"
    )
    assert response.status_code == 200
    deliverables = response.json()["deliverables"]
    assert len(deliverables) > 0

    # Get Deliverable
    deliverable_id = deliverables[0]["id"]
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}"
    )
    assert response.status_code == 200
    deliverable = response.json()
    assert deliverable["id"] == deliverable_id

    ##### Deployments #####

    # Create Deployment
    response = client.post(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
    )
    assert response.status_code == 200
    deployment = response.json()
    assert deployment["id"] is not None
    assert deployment["file_name"] is not None

    # List Deployments
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
    )
    assert response.status_code == 200
    deployments = response.json()["deployments"]
    assert len(deployments) > 0

    # Get Deployment
    deployment_id = deployments[0]["id"]
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}"
    )
    assert response.status_code == 200
    deployment = response.json()
    assert deployment["id"] == deployment_id

    # Delete Deliverable
    response = client.delete(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}"
    )
    assert response.status_code == 200
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/"
    )
    deliverables = response.json()["deliverables"]
    assert next((d for d in deliverables if d["id"] == deliverable_id), None) is None

    # Delete Deployment
    response = client.delete(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/{deployment_id}"
    )
    assert response.status_code == 200
    response = client.get(
        f"{API}/user/{user_id_1}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
    )
    deployments = response.json()["deployments"]
    assert next((d for d in deployments if d["id"] == deployment_id), None) is None
