from codex.providers.ai_provider import AIProvider
from anthropic import AsyncAnthropic


class AnthropicProvider(AIProvider):
    def __init__(self, config):
        super().__init__(config)
        self.client = AsyncAnthropic(**config.get('client_config', {}))

    async def chat(self, req_params):
        model = self.get_model(req_params.get('model'))
        req_params['model'] = model
        req_params["messages"] = [msg for msg in req_params["messages"] if msg["role"] != "system"]

        # Delete the response_format key if it exists
        if "response_format" in req_params:
            del req_params["response_format"]
        return await self.client.messages.create(**req_params)