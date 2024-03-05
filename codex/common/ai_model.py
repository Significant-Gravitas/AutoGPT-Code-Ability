from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

class OpenAIChatClient:
    _instance: "OpenAIChatClient" = None
    _configured = False
    openai: AsyncOpenAI

    @classmethod
    def configure(cls, openai_config):
        if cls._instance is None:
            cls._instance = cls(openai_config)
            cls._configured = True
        else:
            logger.warning("OpenAIChatClient instance has already been configured")

    @classmethod
    def get_instance(cls) -> "OpenAIChatClient":
        if not cls._configured:
            raise Exception("Singleton instance needs to be configured first")
        return cls._instance

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
