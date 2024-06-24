import asyncio
import logging
from typing import Optional, Dict, Any

import tiktoken
from dotenv import load_dotenv

from codex.providers.ai_provider import AIProvider
from codex.providers.anthropic_provider import AnthropicProvider
from codex.providers.groq_provider import GroqProvider
from codex.providers.open_ai_provider import OpenAIProvider

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
    provider: AIProvider
    model: str = 'gpt-4o'
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
            provider_config: Dict[str, Any],
            max_concurrent_ops=100,
            max_requests_per_min=10_000,
            max_tokens_per_min=1_500_000,
    ):
        if cls._instance is None:
            cls.max_concurrent_ops = max_concurrent_ops
            cls.max_requests_per_min = max_requests_per_min
            cls.max_tokens_per_min = max_tokens_per_min

            provider_name = provider_config.get('name', '').lower()
            if provider_name == "openai":
                provider = OpenAIProvider(provider_config)
            elif provider_name == "anthropic":
                provider = AnthropicProvider(provider_config)
            elif provider_name == "groq":
                provider = GroqProvider(provider_config)
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")
            model_name = provider_config.get('model', 'gpt4-o').lower()
            cls.model = model_name
            cls._instance = cls(provider)
            cls._configured = True
            cls._semaphore = asyncio.Semaphore(max_concurrent_ops)
        else:
            logger.warning("AIChatClient instance has already been configured")

    @classmethod
    def get_instance(cls) -> "AIChatClient":
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

            if (
                    cls._total_tokens_count + num_of_tokens_needed
            ) >= cls.max_tokens_per_min:
                time_to_wait = 60 - (current_time - cls._last_request_time)
                if time_to_wait > 0:
                    await asyncio.sleep(time_to_wait)
                cls._total_tokens_count = 0
                cls._last_request_time = current_time

            response = await client.provider.chat(req_params)
            if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                cls._total_tokens_count += response.usage.total_tokens

            return response

    def __init__(self, provider: AIProvider):
        if OpenAIChatClient._configured:
            raise Exception("Singleton instance can only be instantiated once.")
        self.provider = provider



logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import asyncio

    # Example configuration
    provider_config = {
        "name": "openai",
        "client_config": {
            "api_key": "your-api-key-here"
        },
        "models": {
            "gpt3": "gpt-3.5-turbo",
            "gpt4": "gpt-4"
        },
        "default_model": "gpt-3.5-turbo"
    }

    OpenAIChatClient.configure(provider_config=provider_config)
    client = OpenAIChatClient.get_instance()
    request_params = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Answer concisely"},
            {"role": "user", "content": "What is the capital of USA"},
        ],
    }
    response = asyncio.run(OpenAIChatClient.chat(request_params))
    print(response)
