from prisma.enums import DevelopmentPhase

from codex.api_model import Identifiers
from codex.common.ai_block import AIBlock, ValidatedResponse, ValidationError


class DocumentationExtractor(AIBlock):
    """
    This is a block that handles extracting relevant doccumenation from a PyPi README or similar, based on an error message.
    """

    developement_phase = DevelopmentPhase.DEVELOPMENT
    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "validate/documentation_extractor"
    # Model to use for the LLM
    model = "gpt-4o"
    # Should we force the LLM to reply in JSON
    is_json_response = False

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case, we perform some basic checks
        to ensure the response is not empty.
        """
        if not response.response.strip():
            raise ValidationError("Response is empty")

        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database.
        For now, we can just pass since we don't have a specific database model for this.
        """
        pass
