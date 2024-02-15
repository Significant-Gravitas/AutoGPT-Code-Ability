import json
from typing import Dict, Optional

from pydantic import BaseModel

from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)


class SelectNode(BaseModel):
    node_id: str
    input_map: Optional[Dict[str, str]]
    output_map: Optional[Dict[str, str]]

    def __str__(self) -> str:
        out = "Node ID: " + self.node_id + "\n"
        if self.input_map:
            out += "Input Map:\n"
            for k, v in self.input_map.items():
                out += f"\t{k} -> {v}\n"
        if self.output_map:
            out += "Output Map:\n"
            for k, v in self.output_map.items():
                out += f"\t{k} -> {v}\n"
        return out


class SelectFunctionAIBlock(AIBlock):
    prompt_template_name = "select_function"
    model = "gpt-4-0125-preview"
    is_json_response = True

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        json_data = json.loads(response.response)

        try:
            model = SelectNode(**json_data)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")
        return response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        pass
