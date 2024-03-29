import pytest
from dotenv import load_dotenv

load_dotenv()

from codex.develop.code_validation import CodeValidator
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
model Booking {
    id          Int       @id @default(autoincrement())
    status      BookingStatus
    userId      Int
    startTime   DateTime
    endTime     DateTime
}

enum BookingStatus {
    PENDING
    CONFIRMED
    CANCELLED
}
"""


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_simple_function():
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
    # TODO add more validations.


PWUTS_SERVER_CODE = """
import io
import logging
from contextlib import asynccontextmanager

import prisma
import project.cancel_appointment_service
import project.check_availability_service
import project.create_appointment_service
import project.create_profile_service
import project.get_profile_service
import project.login_service
import project.logout_service
import project.reschedule_appointment_service
import project.submit_feedback_service
import project.update_availability_service
import project.update_profile_service
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response, StreamingResponse
from prisma import Prisma

logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.disconnect()


app = FastAPI(
    title="Availability Checker",
    lifespan=lifespan,
    description=\"\"\"To implement a function that returns the real-time availability of professionals, updating based on current activity or schedule, you'll build on the technologies and approaches discussed previously. Here's a comprehensive overview blending all gathered insights:

1. **Tech Stack**:
   - Programming Language: Python
   - API Framework: FastAPI
   - Database: PostgreSQL
   - ORM: Prisma

2. **Functionality Overview**:
   Your application will allow users to check the real-time availability of professionals, taking into account their current activity and future schedules. This involves a back-end service that interacts with a PostgreSQL database to store and manage professional availability information.

3. **Development Steps**:
   a. Initialize your FastAPI project and set up your development environment. Include essential libraries and tools, such as Uvicorn for serving your application.
   b. Utilize Prisma to define your database schema. Your `schema.prisma` file should include models for professionals, their services, schedules, and availability status.
   c. Generate Prisma Client to interact with your database efficiently.
   d. Implement the functionality to check real-time availability within a FastAPI endpoint (e.g., '/check-availability'). This endpoint should accept relevant parameters (e.g., professional ID, service type) and return the professional's availability status.
   e. Build a function that updates professionals' availability in real-time. This can be based on their current activities (e.g., ongoing appointments) and scheduled future activities. Consider the use of background tasks or webhooks to update availability status based on real-time events.

4. **Best Practices**:
   - Employ WebSockets for real-time updates where applicable, especially for notifying users about changes in availability.
   - Ensure robust error handling and validation to provide clear feedback and prevent incorrect availability status.
   - Optimize your database queries for performance, especially if you're checking availability in real-time for a large number of professionals.

5. **Security and Compliance**:
   Implement secure access controls and authentication to protect sensitive data. Ensure your application complies with relevant data protection and privacy regulations.

6. **Testing and Deployment**:
   Before deploying your application, thoroughly test the availability checking functionality and real-time updates. Use tools like Swagger UI to test your FastAPI endpoints.

This plan provides a detailed roadmap to develop a system that efficiently manages and displays the real-time availability of professionals, enhancing user experience by allowing for advanced scheduling and immediate availability checks.\"\"\",
)


@app.post(
    "/appointments/create",
    response_model=project.create_appointment_service.CreateAppointmentResponse,
)
async def api_post_create_appointment(
    clientId: str,
    professionalId: str,
    serviceId: str,
    startTime: datetime,
    endTime: datetime,
    notes: Optional[str],
) -> project.create_appointment_service.CreateAppointmentResponse | Response:
    \"\"\"
    Schedule a new appointment.
    \"\"\"
    try:
        res = await project.create_appointment_service.create_appointment(
            clientId, professionalId, serviceId, startTime, endTime, notes
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
    "/feedback/submit",
    response_model=project.submit_feedback_service.FeedbackSubmissionResponse,
)
async def api_post_submit_feedback(
    userId: Optional[str], content: str, rating: Optional[int]
) -> project.submit_feedback_service.FeedbackSubmissionResponse | Response:
    \"\"\"
    Allows users to submit feedback about the platform.
    \"\"\"
    try:
        res = await project.submit_feedback_service.submit_feedback(
            userId, content, rating
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


@app.post("/auth/logout", response_model=project.logout_service.LogoutResponse)
async def api_post_logout(
    Authorization: str,
) -> project.logout_service.LogoutResponse | Response:
    \"\"\"
    Terminates an active user session.
    \"\"\"
    try:
        res = await project.logout_service.logout(Authorization)
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
    "/appointments/{appointmentId}/reschedule",
    response_model=project.reschedule_appointment_service.RescheduleAppointmentResponse,
)
async def api_put_reschedule_appointment(
    appointmentId: str, newStartTime: datetime, newEndTime: datetime
) -> project.reschedule_appointment_service.RescheduleAppointmentResponse | Response:
    \"\"\"
    Reschedule an existing appointment.
    \"\"\"
    try:
        res = await project.reschedule_appointment_service.reschedule_appointment(
            appointmentId, newStartTime, newEndTime
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
    "/appointments/{appointmentId}/cancel",
    response_model=project.cancel_appointment_service.CancelAppointmentResponse,
)
async def api_delete_cancel_appointment(
    appointmentId: str,
) -> project.cancel_appointment_service.CancelAppointmentResponse | Response:
    \"\"\"
    Cancel an existing appointment.
    \"\"\"
    try:
        res = await project.cancel_appointment_service.cancel_appointment(appointmentId)
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
    "/availability/update",
    response_model=project.update_availability_service.UpdateAvailabilityResponse,
)
async def api_post_update_availability(
    professional_id: str,
    availability_status: bool,
    start_time: datetime,
    end_time: datetime,
) -> project.update_availability_service.UpdateAvailabilityResponse | Response:
    \"\"\"
    Updates a professional's availability status.
    \"\"\"
    try:
        res = await project.update_availability_service.update_availability(
            professional_id, availability_status, start_time, end_time
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
    "/profiles/create",
    response_model=project.create_profile_service.CreateUserProfileResponse,
)
async def api_post_create_profile(
    userId: str,
    fullName: str,
    servicesOffered: Optional[List[str]],
    contactInformation: project.create_profile_service.ContactInformation,
) -> project.create_profile_service.CreateUserProfileResponse | Response:
    \"\"\"
    Creates a new user profile.
    \"\"\"
    try:
        res = await project.create_profile_service.create_profile(
            userId, fullName, servicesOffered, contactInformation
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
    "/profiles/{userId}/update",
    response_model=project.update_profile_service.UpdateUserProfileResponse,
)
async def api_put_update_profile(
    userId: str, full_name: str, email: str, phone: str, services_offered: List[str]
) -> project.update_profile_service.UpdateUserProfileResponse | Response:
    \"\"\"
    Updates a user profile details.
    \"\"\"
    try:
        res = await project.update_profile_service.update_profile(
            userId, full_name, email, phone, services_offered
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


@app.get(
    "/availability/check",
    response_model=project.check_availability_service.CheckAvailabilityResponse,
)
async def api_get_check_availability(
    professional_id: str,
    service_type: Optional[str],
    start_time: datetime,
    end_time: datetime,
) -> project.check_availability_service.CheckAvailabilityResponse | Response:
    \"\"\"
    Checks a professional's availability based on input parameters.
    \"\"\"
    try:
        res = await project.check_availability_service.check_availability(
            professional_id, service_type, start_time, end_time
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


@app.get(
    "/profiles/{userId}", response_model=project.get_profile_service.GetProfileResponse
)
async def api_get_get_profile(
    userId: str,
) -> project.get_profile_service.GetProfileResponse | Response:
    \"\"\"
    Retrieves a user profile based on the user ID.
    \"\"\"
    try:
        res = await project.get_profile_service.get_profile(userId)
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


@app.post("/auth/login", response_model=project.login_service.LoginResponse)
async def api_post_login(
    email: str, password: str
) -> project.login_service.LoginResponse | Response:
    \"\"\"
    Authenticates users and returns a session token.
    \"\"\"
    try:
        res = await project.login_service.login(email, password)
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

@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_pwuts_function():
    validator = CodeValidator(
        compiled_route_id="test_1",
        database_schema=SAMPLE_SCHEMA,
    )
    response = await validator.reformat_code(
        PWUTS_SERVER_CODE,
        [Package(package_name="fastapi"), Package(package_name="prisma")],
    )
    assert "from datetime import datetime" in response
    assert "from typing import List, Optional" in response
    # TODO add more validations.