from codex.providers.ai_provider import AIProvider
from groq import Groq


class GroqProvider(AIProvider):
    def __init__(self, config):
        super().__init__(config)

        self.client = Groq(**config.get('client_config', {}))

    async def chat(self, req_params):
        model = self.get_model(req_params.get('model'))
        req_params['model'] = model
        return await self.client.chat.completions.create(**req_params)