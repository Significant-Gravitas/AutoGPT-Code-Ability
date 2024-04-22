import asyncio
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
    max_concurrent_ops: int = 1_000
    max_requests_per_min: int = 300
    _semaphore: asyncio.Semaphore
    _request_count: int = 0
    _last_request_time: float = 0

    @classmethod
    def configure(
        cls, openai_config, max_concurrent_ops=1_000, max_requests_per_min=10_000
    ):
        if cls._instance is None:
            if "model" in openai_config:
                cls.chat_model = openai_config["model"]
                del openai_config["model"]
            if "max_tokens" in openai_config:
                cls.max_tokens = openai_config["max_tokens"]
                del openai_config["max_tokens"]
            cls.max_concurrent_ops = max_concurrent_ops
            cls.max_requests_per_min = max_requests_per_min
            cls._instance = cls(openai_config)
            cls._configured = True
            cls._semaphore = asyncio.Semaphore(max_concurrent_ops)
        else:
            logger.warning("OpenAIChatClient instance has already been configured")

    @classmethod
    def get_instance(cls) -> "OpenAIChatClient":
        if not cls._configured or cls._instance is None:
            raise Exception("Singleton instance needs to be configured first")
        return cls._instance

    @classmethod
    async def chat(cls, req_params):
        client = cls.get_instance()
        async with cls._semaphore:
            current_time = asyncio.get_running_loop().time()
            if current_time - cls._last_request_time >= 60:
                cls._request_count = 0
                cls._last_request_time = current_time
            if cls._request_count >= cls.max_requests_per_min:
                await asyncio.sleep(60 - (current_time - cls._last_request_time))
                cls._request_count = 0
                cls._last_request_time = current_time
            if cls.chat_model:
                req_params["model"] = cls.chat_model
            if cls.max_tokens:
                req_params["max_tokens"] = cls.max_tokens
            cls._request_count += 1
            return await client.openai.chat.completions.create(**req_params)

    def __init__(self, openai_config):
        if OpenAIChatClient._configured:
            raise Exception("Singleton instance can only be instantiated once.")
        self.openai = AsyncOpenAI(**openai_config)


logger = logging.getLogger(__name__)


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
