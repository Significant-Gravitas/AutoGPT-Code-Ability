import json

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.developer.model import CheckComplexity


class CheckComplexityAIBlock(AIBlock):
    prompt_template_name = "check_code_complexity"
    model = "gpt-4-0125-preview"
    is_json_response = True

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        json_data = json.loads(response.response)

        try:
            model = CheckComplexity(**json_data)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        pass
