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
        message=chat,
    )


@chat_router.post(
    "/user/{user_id}/apps/{app_id}/chat/{chat_id}/continue",
    response_model=codex.chat.model.ChatResponse,
)
async def continue_chat(
    user_id: str, app_id: str, chat_id: str, request: codex.chat.model.ChatRequest
) -> Response | codex.chat.model.ChatResponse:
    """
    Keep the conversation going

    Parameters:
    - user_id (str): The ID of the user
    - app_id (str): The ID of the application
    - chat_id (str): The ID of the chat
    - request (ChatRequest): The user's chat request

    Returns:
    - Response: The response object containing the chat continuation

    Description:
    This function is used to continue the conversation in a chat. It takes the user ID,
    application ID, chat ID, and the user's message as input parameters. It retrieves the
    application and user information from the database using the provided IDs. Then, it
    creates an instance of the Identifiers class with the user ID, application ID, and
    cloud services ID. Finally, it calls the continue_chat() function from the
    codex.chat.agent module to continue the chat and returns the response object
    containing the chat continuation.

    Example:
    continue_chat("user123", "app456", "chat789", ChatRequest(message="Hello"))
    """
    logger.info(f"Chat: {chat_id} Next request received: {request.message}")
    app = await codex.database.get_app_by_id(user_id, app_id)
    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )
    chat = await codex.chat.agent.continue_chat(ids, app, request)
    return codex.chat.model.ChatResponse(
        message=chat,
    )
