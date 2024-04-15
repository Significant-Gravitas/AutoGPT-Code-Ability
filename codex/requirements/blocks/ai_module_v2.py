import logging

import pydantic

import codex.common.ai_block


class Module(pydantic.BaseModel):
    """
    A Software Module for the application
    """

    name: str
    description: str


class ModuleResponse(pydantic.BaseModel):
    """
    This is the response model for the ModuleGenerationBlock
    """

    thoughts: str
    say: str
    modules: list[Module]
    access_roles: list[str]


logger = logging.getLogger(__name__)


class ModuleGenerationBlock(codex.common.ai_block.AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/module/generation"
    # Model to use for the LLM
    model = "gpt-4-turbo"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = ModuleResponse

    async def validate(
        self, invoke_params: dict, response: codex.common.ai_block.ValidatedResponse
    ) -> codex.common.ai_block.ValidatedResponse:
        try:
            model = ModuleResponse.model_validate_json(response.response, strict=False)
            response.response = model
        except Exception as e:
            raise codex.common.ai_block.ValidationError(
                f"Error validating response: {e}"
            )

        return response

    async def create_item(
        self,
        ids: codex.common.ai_block.Identifiers,
        validated_response: codex.common.ai_block.ValidatedResponse,
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass
