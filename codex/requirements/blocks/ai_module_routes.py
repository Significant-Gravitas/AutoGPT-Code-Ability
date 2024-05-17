import logging

import prisma
import prisma.enums
import pydantic

import codex.common.ai_block


class APIRoute(pydantic.BaseModel):
    """
    A Software Module for the application
    """

    http_verb: prisma.enums.HTTPVerb
    function_name: str
    path: str
    description: str
    access_level: prisma.enums.AccessLevel
    allowed_access_roles: list[str]


class ModuleApiRouteResponse(pydantic.BaseModel):
    """
    This is the response model for the ModuleGenerationBlock
    """

    thoughts: str
    say: str
    routes: list[APIRoute]


logger = logging.getLogger(__name__)


class ModuleGenerationBlock(codex.common.ai_block.AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/module_routes"
    # Model to use for the LLM
    model = "gpt-4o"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = ModuleApiRouteResponse

    async def validate(
        self, invoke_params: dict, response: codex.common.ai_block.ValidatedResponse
    ) -> codex.common.ai_block.ValidatedResponse:
        try:
            model = ModuleApiRouteResponse.model_validate_json(
                response.response, strict=False
            )
            # Force set the allowed_access_roles to empty list for public routes
            for route in model.routes:
                if route.access_level == prisma.enums.AccessLevel.PUBLIC:
                    route.allowed_access_roles = []
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
