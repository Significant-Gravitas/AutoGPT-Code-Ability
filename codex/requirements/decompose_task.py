import json
from typing import List

from pydantic import BaseModel

from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.requirements.model import DecomposeTaskModel


## TEMP
class ExecutionPath(BaseModel):
    name: str
    endpoint_name: str
    description: str


class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str


class DecomposeTaskAIBlock(AIBlock):
    prompt_template_name = "decompose_task"
    model = "gpt-4-0125-preview"
    is_json_response = True

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        json_data = json.loads(response.response)

        try:
            model = DecomposeTaskModel(**json_data)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        pass
