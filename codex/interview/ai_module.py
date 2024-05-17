import logging

import prisma.models

import codex.common.ai_block
import codex.interview.model

logger = logging.getLogger(__name__)


class ModuleGenerationBlock(codex.common.ai_block.AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "interview/module"
    # Model to use for the LLM
    model = "gpt-4o"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = codex.interview.model.ModuleResponse

    @staticmethod
    def create_modules_list(features: list[prisma.models.Module]):
        modules_section = ""
        for i, f in enumerate(features):
            modules_section += f"{i}: {f.name} - {f.description}\n"
        return modules_section

    async def validate(
        self, invoke_params: dict, response: codex.common.ai_block.ValidatedResponse
    ) -> codex.common.ai_block.ValidatedResponse:
        try:
            model = codex.interview.model.ModuleResponse.model_validate_json(
                response.response, strict=False
            )
            if model.phase_completed and model.modules is not None:
                raise codex.common.ai_block.ValidationError(
                    "Phase completed, no more modules changes can be made, do not add any!"
                )
            if model.modules:
                for m in model.modules:
                    if m.action not in ["add", "remove", "update"]:
                        raise codex.common.ai_block.ValidationError(
                            f"Invalid action: {m.action} only 'add', 'remove', 'update' are allowed"
                        )
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
