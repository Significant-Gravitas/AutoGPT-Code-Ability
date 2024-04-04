import pytest
from dotenv import load_dotenv

from codex.common.ai_block import LineValidationError, ValidationError
from codex.develop.code_validation import CodeValidator, append_errors_as_todos
from codex.develop.model import Package

load_dotenv()

SERVER_CODE_SAMPLE = """
import io
import logging
from contextlib import asynccontextmanager
from datetime import datetime

import prisma
import project.cancel_booking_service
import project.create_booking_service
import project.get_user_preferences_service
import project.send_notification_service
import project.subscribe_availability_updates_service
import project.update_booking_service
import project.update_user_preferences_service
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)

db_client = prisma.Prisma(auto_register=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.disconnect()


app = FastAPI(
    title="Availability Checker",
    lifespan=lifespan,
    description=\"\"\"To achieve the task of returning the real-time availability of professionals, updating based on current activity or schedule, a comprehensive system needs to be designed and implemented. Based on our discussions and findings, the following summary outlines key aspects and recommendations for this system:

1. **Real-Time Update Mechanism**: Leveraging WebSockets for bi-directional communication between the server and clients offers an efficient way to push updates to clients as soon as they happen. This choice is crucial for ensuring that the information about professionals' availability is updated in real-time.

2. **System Design Components**: The design incorporates several core components:
  - **Data Store**: PostgreSQL database, chosen for its reliability and support for complex queries that may be required when handling professionals' schedules and availability.
  - **Application Layer**: FastAPI is recommended for the backend due to its asynchronous support which aligns well with real-time data handling and its ease of setting up WebSockets. FastAPI will handle the business logic related to professionals' schedules and availability.
  - **ORM**: Prisma is selected to interact with the PostgreSQL database. It provides a nice abstraction and simplifies database operations, making it easier to manage the data model for professionals' schedules.
  - **API Layer**: FastAPI will also serve the role of providing API endpoints that the frontend can use to fetch or subscribe to availability updates.
  - **Front-end Interface**: The front end should implement WebSocket clients to receive real-time updates from the server. Details about implementing this are dependent on the chosen front-end technology.
  - **Notification System**: Optionally, for immediate alerts to users or professionals about changes in availability, integrating a notification system can be beneficial.
  - **Caching**: Implementing caching mechanisms to store frequently accessed data reduces database load and improves performance.

3. **Challenges and Considerations**: Handling concurrent requests and updates efficiently is vital. Techniques like database replication, sharding, and load balancing may be necessary as the system scales. Monitoring tools should be integrated to track system performance and user activities.

This comprehensive approach caters to the requirements of creating a real-time availability system for professionals, updating based on their current activity or schedule. It maps out the technology stack and architectural considerations vital for such a system.\"\"\",
)


@app.get(
    "/subscribe/availability",
    response_model=project.subscribe_availability_updates_service.SubscribeAvailabilityUpdatesResponse,
)
async def api_get_subscribe_availability_updates(
    request: project.subscribe_availability_updates_service.SubscribeAvailabilityUpdatesRequest,
) -> project.subscribe_availability_updates_service.SubscribeAvailabilityUpdatesResponse | Response:
    \"\"\"
    Endpoint for clients to initiate a WebSocket connection for receiving real-time availability updates.
    \"\"\"
    try:
        res = await project.subscribe_availability_updates_service.subscribe_availability_updates(
            request
        )
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.delete(
    "/bookings/{id}",
    response_model=project.cancel_booking_service.CancelBookingResponse,
)
async def api_delete_cancel_booking(
    id: str,
) -> project.cancel_booking_service.CancelBookingResponse | Response:
    \"\"\"
    Cancel an existing booking.
    \"\"\"
    try:
        res = await project.cancel_booking_service.cancel_booking(id)
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.get(
    "/preferences",
    response_model=project.get_user_preferences_service.UserPreferencesResponse,
)
async def api_get_get_user_preferences(
    request: project.get_user_preferences_service.GetUserPreferencesRequest,
) -> project.get_user_preferences_service.UserPreferencesResponse | Response:
    \"\"\"
    Fetch the current user preferences.
    \"\"\"
    try:
        res = await project.get_user_preferences_service.get_user_preferences(request)
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.put(
    "/preferences",
    response_model=project.update_user_preferences_service.UpdateUserPreferencesResponse,
)
async def api_put_update_user_preferences(
    userId: str, notifyByEmail: bool, notifyBySMS: bool
) -> project.update_user_preferences_service.UpdateUserPreferencesResponse | Response:
    \"\"\"
    Update user preferences.
    \"\"\"
    try:
        res = await project.update_user_preferences_service.update_user_preferences(
            userId, notifyByEmail, notifyBySMS
        )
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.post(
    "/notifications/send",
    response_model=project.send_notification_service.SendNotificationResponse,
)
async def api_post_send_notification(
    userId: str, content: str, channel: str, eventType: str
) -> project.send_notification_service.SendNotificationResponse | Response:
    \"\"\"
    Send a custom notification to a user.
    \"\"\"
    try:
        res = await project.send_notification_service.send_notification(
            userId, content, channel, eventType
        )
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.put(
    "/bookings/{id}",
    response_model=project.update_booking_service.BookingUpdateResponse,
)
async def api_put_update_booking(
    id: str,
    scheduledStartTime: datetime,
    scheduledEndTime: datetime,
    status: BookingStatus,
) -> project.update_booking_service.BookingUpdateResponse | Response:
    \"\"\"
    Update details of an existing booking.
    \"\"\"
    try:
        res = await project.update_booking_service.update_booking(
            id, scheduledStartTime, scheduledEndTime, status
        )
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )


@app.post(
    "/bookings", response_model=project.create_booking_service.CreateBookingOutput
)
async def api_post_create_booking(
    service_seeker_id: str,
    professional_id: str,
    scheduled_start_time: datetime,
    scheduled_end_time: datetime,
    details: Optional[str],
) -> project.create_booking_service.CreateBookingOutput | Response:
    \"\"\"
    Create a new booking with a professional.
    \"\"\"
    try:
        res = await project.create_booking_service.create_booking(
            service_seeker_id,
            professional_id,
            scheduled_start_time,
            scheduled_end_time,
            details,
        )
        return res
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] = str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )
"""

SAMPLE_SCHEMA = """
enum BookingStatus {
    PENDING
    CONFIRMED
    CANCELLED
}

model Booking {
    id String @id @default(cuid())
    status BookingStatus
    scheduledStartTime DateTime
    scheduledEndTime DateTime
}
"""


@pytest.mark.asyncio
async def test_server_code():
    validator = CodeValidator(
        compiled_route_id="test_1",
        database_schema=SAMPLE_SCHEMA,
    )
    response = await validator.reformat_code(
        SERVER_CODE_SAMPLE,
        [Package(package_name="fastapi"), Package(package_name="prisma")],
    )
    assert "prisma.enums.BookingStatus" in response
    assert "from typing import Optional" in response
    assert "TODO" not in response
    # TODO add more validations.


SIMPLE_FUNCTION = """
def hello_world():
    return "Hello World"

hello_world() # comment
""".strip()

EXPECTED_TODOS = """
# TODO(autogpt): First Error
# TODO(autogpt): Second Error
#     Second Error continuation
def hello_world():
    return "Hello World" # TODO(autogpt): Third Error
#   Third Error continuation

hello_world() # comment # TODO(autogpt): Fourth Error
""".strip()


def test_append_errors_as_todos():
    code = SIMPLE_FUNCTION
    response = append_errors_as_todos(
        [
            LineValidationError("Third Error\nThird Error continuation", code, 2),
            LineValidationError("Fourth Error", code, 4),
            ValidationError("Second Error\nSecond Error continuation"),
            ValidationError("First Error"),
        ],
        code,
    )
    assert response == EXPECTED_TODOS
