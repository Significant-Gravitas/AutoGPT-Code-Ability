import logging
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIChatClient:
    _instance: Optional["OpenAIChatClient"] = None
    _configured = False
    openai: AsyncOpenAI
    chat_model: str | None = None
    max_tokens: int | None = None

    @classmethod
    def configure(cls, openai_config):
        if cls._instance is None:
            if "model" in openai_config:
                cls.chat_model = openai_config["model"]
                del openai_config["model"]
            if "max_tokens" in openai_config:
                cls.max_tokens = openai_config["max_tokens"]
                del openai_config["max_tokens"]

            cls._instance = cls(openai_config)

            cls._configured = True
        else:
            logger.warning("OpenAIChatClient instance has already been configured")

    @classmethod
    def get_instance(cls) -> "OpenAIChatClient":
        if not cls._configured or cls._instance is None:
            raise Exception("Singleton instance needs to be configured first")
        return cls._instance

    @classmethod
    def chat(cls, req_params):
        if cls.chat_model:
            req_params["model"] = cls.chat_model
        if cls.max_tokens:
            req_params["max_tokens"] = cls.max_tokens
        client = cls.get_instance()
        return client.openai.chat.completions.create(**req_params)

    def __init__(self, openai_config):
        if OpenAIChatClient._configured:
            raise Exception("Singleton instance can only be instantiated once.")
        self.openai = AsyncOpenAI(**openai_config)


if __name__ == "__main__":
    import asyncio

    OpenAIChatClient.configure(openai_config={})
    client = OpenAIChatClient.get_instance()
    request_params = {
        "model": "gpt-3.5-turbo",
        "messges": [
            {"role": "system", "content": "Answer dead good"},
            {"role": "user", "content": "What is the capital of USA"},
        ],
    }
    response = asyncio.run(
        client.openai.chat.completions.create(
            model=request_params["model"], messages=request_params["messges"]
        )
    )
    print(response)
