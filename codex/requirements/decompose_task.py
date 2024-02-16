import json
from typing import List

from pydantic import BaseModel

from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.requirements.model import FeaturesSuperObject


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
    pydantic_object = FeaturesSuperObject

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        json_data = json.loads(response.response)

        try:
            model = FeaturesSuperObject(**json_data)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        pass


if __name__ == "__main__":
    import asyncio

    import prisma

    from codex.api_model import Indentifiers

    db_client = prisma.Prisma(auto_register=True)
    test = DecomposeTaskAIBlock()
    ids = Indentifiers(
        user_id=1,
        app_id=1,
        spec_id=1,
        completed_app_id=1,
    )

    async def run_me():
        await db_client.connect()
        await test.invoke(ids, {})
        await db_client.disconnect()

    asyncio.run(run_me())
