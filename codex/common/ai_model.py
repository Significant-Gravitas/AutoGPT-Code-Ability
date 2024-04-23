import logging
from typing import Optional

import litellm

logger = logging.getLogger(__name__)


class AIChatClient:
    _instance = None
    _configured = False
    override_model: Optional[str] = None
    override_max_tokens: Optional[int] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIChatClient, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance

    @classmethod
    def configure(
        cls,
        override_model: Optional[str] = None,
        override_max_tokens: Optional[int] = None,
    ):
        if not cls._configured:
            cls.override_model = override_model
            cls.override_max_tokens = override_max_tokens
            cls._configured = True
        else:
            logger.warning("AIChatClient instance has already been configured")

    @classmethod
    async def chat(cls, req_params) -> litellm.ModelResponse:
        if cls.override_model:
            req_params["model"] = cls.override_model
        if cls.override_max_tokens:
            req_params["max_tokens"] = cls.override_max_tokens
        if "stream" in req_params:
            del req_params["stream"]
            logger.warning("Stream is not supported in this client")
        # Assuming `litellm.acompletion` is a method from an imported library
        response = await litellm.acompletion(**req_params)
        if isinstance(response, litellm.ModelResponse):
            return response
        else:
            raise ValueError(
                f"Received invalid response from AI model, {type(response)}"
            )


if __name__ == "__main__":
    import asyncio

    AIChatClient.configure()
    request_params = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Answer dead good"},
            {"role": "user", "content": "What is the capital of USA"},
        ],
    }
    response = asyncio.run(AIChatClient.chat(request_params))
    print(response)
