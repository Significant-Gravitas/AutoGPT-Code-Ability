from codex.common.ai_block import AIBlock, ValidatedResponse, ValidationError
from codex.requirements.model import DecomposeTaskModel
from typing import List 
from pydantic import BaseModel
import json


## TEMP
class ExecutionPath(BaseModel):
    name: str
    endpoint_name: str
    description: str


class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str


class DecomposeTaskAIBlock(AIBlock):
    
    def validate(self, invoke_params: dict, response: ValidatedResponse) -> ValidatedResponse:
        json_data = json.loads(response.response)
        
        try:
            model = DecomposeTaskModel(**json_data)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")
        
        return response
    
    async def create_item(self, validated_response: ValidatedResponse):
        """ This is just a temporary that doesnt have a database model"""
        pass
