import logging

from pydantic import ValidationError

from codex.common.ai_block import AIBlock, Identifiers, ValidatedResponse
from codex.common.logging_config import setup_logging
from codex.interview.model import InterviewMessageWithResponseOptionalId

logger = logging.getLogger(__name__)


class AskBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/interview/ask"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = InterviewMessageWithResponseOptionalId

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: InterviewMessageWithResponseOptionalId = (
                InterviewMessageWithResponseOptionalId.model_validate_json(
                    response.response
                )
            )
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass


if __name__ == "__main__":
    """
    This is a simple test to run the block
    """
    from asyncio import run

    from prisma import Prisma

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging(local=True)

    OpenAIChatClient.configure({})
    db_client = Prisma(auto_register=True)

    ask_block = AskBlock()

    async def run_ai() -> dict[str, InterviewMessageWithResponseOptionalId]:
        await db_client.connect()
        memory: list[InterviewMessageWithResponseOptionalId] = []
        response_ref: InterviewMessageWithResponseOptionalId = await ask_block.invoke(
            ids=ids,
            invoke_params={
                "content": "Do you prefer signing up with OAuth2 providers or traditional sign-in methods for your applications?",
                "memory": memory,
            },
        )

        await db_client.disconnect()
        return {
            "response_ref": response_ref,
        }

    responses = run(run_ai())

    for key, item in responses.items():
        if isinstance(item, InterviewMessageWithResponseOptionalId):
            logger.info(f"\t{item.tool}: {item.content}: {item.response}")
        else:
            logger.info(f"{key}: {item}")
            breakpoint()
