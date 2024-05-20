import logging

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

import codex.database
import codex.interview.agent
import codex.interview.database
from codex.api_model import Identifiers, InterviewNextRequest
from codex.interview.model import InterviewResponse

logger = logging.getLogger(__name__)

interview_router = APIRouter(
    tags=["interview"],
)


@interview_router.post(
    "/user/{user_id}/apps/{app_id}/interview/", response_model=InterviewResponse
)
async def start_interview(
    user_id: str,
    app_id: str,
) -> Response | InterviewResponse:
    """
    Create a new Interview for a given application and user.
    """
    app = await codex.database.get_app_by_id(user_id, app_id)
    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )

    interview = await codex.interview.agent.start_interview(ids=ids, app=app)

    return interview


@interview_router.post(
    "/user/{user_id}/apps/{app_id}/interview/{interview_id}/next",
    response_model=InterviewResponse,
)
async def take_next_step(
    user_id: str, app_id: str, interview_id: str, next_request: InterviewNextRequest
) -> Response | InterviewResponse:
    """
    Keep working through the interview until it is finished
    """
    user_message = next_request.msg
    logger.info(f"Interview: {interview_id} Next request recieved: {user_message}")
    app = await codex.database.get_app_by_id(user_id, app_id)
    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        interview_id=interview_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )

    response = await codex.interview.agent.continue_interview(
        ids=ids, app=app, user_message=user_message
    )
    return response


@interview_router.delete("/user/{user_id}/apps/{app_id}/interview/{interview_id}")
async def delete_interview(user_id: str, app_id: str, interview_id: str):
    """
    Delete a specific interview by its ID for a given application and user.
    """
    await codex.interview.database.delete_interview(interview_id)
    return JSONResponse(
        content={"message": "Interview deleted successfully"},
        status_code=200,
    )
