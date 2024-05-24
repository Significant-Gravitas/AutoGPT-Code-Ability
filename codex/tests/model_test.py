import pytest
from dotenv import load_dotenv

from codex.api_model import ObjectFieldModel, ObjectTypeModel
from codex.app import db_client
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.model import create_object_type

load_dotenv()
setup_logging()


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_create_nested_object_type():
    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})
    await db_client.connect()

    object_type = ObjectTypeModel(
        name="SyncExternalCalendarRequest",
        description="Request model for synchronizing a professional's schedule with an external calendar service. Includes credentials for accessing the external calendar, as well as the ID of the professional's schedule to be synchronized.",
        Fields=[
            ObjectFieldModel(
                name="scheduleId",
                description="The unique identifier for the professional's schedule to synchronize.",
                type="int",
            ),
            ObjectFieldModel(
                name="syncOptions",
                description="Optional parameters defining how the synchronization should be performed.",
                type="SyncOptions",
                related_types=[
                    ObjectTypeModel(
                        name="SyncOptions",
                        description="Defines options for how the synchronization with an external calendar is performed.",
                        Fields=[
                            ObjectFieldModel(
                                name="importAppointments",
                                description="Whether to import appointments from the external calendar into the ProfAvail schedule.",
                                type="bool",
                            ),
                            ObjectFieldModel(
                                name="exportAppointments",
                                description="Whether to export appointments from the ProfAvail schedule to the external calendar.",
                                type="bool",
                            ),
                            ObjectFieldModel(
                                name="syncRange",
                                description="The range of dates to synchronize, formatted as 'YYYY-MM-DD to YYYY-MM-DD'.",
                                type="str",
                            ),
                        ],
                    )
                ],
            ),
        ],
    )
    created_objects = await create_object_type(object_type, {})
    assert created_objects is not None
    assert len(created_objects) == 2

    assert "SyncExternalCalendarRequest" in created_objects
    assert created_objects["SyncExternalCalendarRequest"] is not None
    assert len(created_objects["SyncExternalCalendarRequest"].Fields) == 2  # type: ignore
    assert (
        len(created_objects["SyncExternalCalendarRequest"].Fields[1].RelatedTypes) == 1  # type: ignore
    )

    assert "SyncOptions" in created_objects
    assert created_objects["SyncOptions"] is not None
