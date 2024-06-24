import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import tiktoken
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# Keep the num_tokens_from_messages function as is

class AIProvider(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get('model', '')
        self.default_model = config.get('default_model')

    @abstractmethod
    async def chat(self, req_params: Dict[str, Any]):
        pass

    def get_model(self, model_name: Optional[str] = None) -> str:
        if self.model:
            return self.model
        return self.default_model



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

    AIChatClient.configure(provider_config=provider_config)
    client = AIChatClient.get_instance()
    request_params = {
        "model": "gpt3",  # This will be mapped to "gpt-3.5-turbo"
        "messages": [
            {"role": "system", "content": "Answer concisely"},
            {"role": "user", "content": "What is the capital of USA"},
        ],
    }
    response = asyncio.run(AIChatClient.chat(request_params))
    print(response)