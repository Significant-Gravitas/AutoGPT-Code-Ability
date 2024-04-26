import logging

from fastapi import APIRouter, Response

import codex.chat.agent
import codex.chat.model
import codex.database
from codex.api_model import Identifiers

logger = logging.getLogger(__name__)

chat_router = APIRouter(
    tags=["chat"],
)


@chat_router.post(
    "/user/{user_id}/apps/{app_id}/chat/", response_model=codex.chat.model.ChatResponse
)
async def start_chat(
    user_id: str, app_id: str, request: codex.chat.model.ChatRequest
) -> Response | codex.chat.model.ChatResponse:
    """
    Start a chat session.

    Args:
        user_id (str): The ID of the user initiating the chat.
        app_id (str): The ID of the app associated with the chat.
        request (codex.chat.model.ChatRequest): The chat request object.

    Returns:
        Response: The response object containing the chat content and status code.
    """
    app = await codex.database.get_app_by_id(user_id, app_id)

    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )
    chat = await codex.chat.agent.start_chat(ids, app, request)
    return codex.chat.model.ChatResponse(
        id="",
        message=chat,
    )
