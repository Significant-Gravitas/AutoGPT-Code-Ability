import asyncio
import logging
from typing import Optional

import tiktoken
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

from openai import AsyncOpenAI  # noqa


def num_tokens_from_messages(messages):
    """Just a rough estimate here."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4o")
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


class OpenAIChatClient:
    _instance: Optional["OpenAIChatClient"] = None
    _configured = False
    openai: AsyncOpenAI
    chat_model: str | None = None
    max_tokens: int | None = None
    max_concurrent_ops: int = 100
    max_requests_per_min: int = 300
    max_tokens_per_min: int = 1_500_000
    _semaphore: asyncio.Semaphore
    _request_count: int = 0
    _last_request_time: float = 0
    _total_tokens_count: int = 0

    @classmethod
    def configure(
        cls,
        openai_config,
        max_concurrent_ops=100,
        max_requests_per_min=10_000,
        max_tokens_per_min=1_500_000,
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
            cls.max_tokens_per_min = max_tokens_per_min
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
        MAX_COMPLETION_TOKENS = 4095
        num_of_tokens_needed = (
            num_tokens_from_messages(req_params["messages"]) + MAX_COMPLETION_TOKENS
        )

        async with cls._semaphore:
            current_time = asyncio.get_running_loop().time()

            # Check if the token limit per minute has been reached
            if (
                cls._total_tokens_count + num_of_tokens_needed
            ) >= cls.max_tokens_per_min:
                # Calculate the time to wait until the next minute
                time_to_wait = 60 - (current_time - cls._last_request_time)
                if time_to_wait > 0:
                    await asyncio.sleep(time_to_wait)
                cls._total_tokens_count = 0
                cls._last_request_time = current_time

            if cls.chat_model:
                req_params["model"] = cls.chat_model
            if cls.max_tokens:
                req_params["max_tokens"] = cls.max_tokens

            response = await client.openai.chat.completions.create(**req_params)
            if response.usage and response.usage.total_tokens:
                cls._total_tokens_count += response.usage.total_tokens

            return response

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
