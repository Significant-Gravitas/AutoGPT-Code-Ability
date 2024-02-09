import json
from typing import List

from pydantic import BaseModel

from codex.api_model import Indentifiers
from codex.common.ai_block import AIBlock, ValidatedResponse, ValidationError
from codex.requirements.model import Clarification


class ClarifyBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/clarify_task"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = Clarification

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = Clarification.model_validate_json(response.response)
            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
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

    from openai import OpenAI
    from prisma import Prisma

    from codex.api_model import Indentifiers

    ids = Indentifiers(user_id=1, app_id=1)
    db_client = Prisma(auto_register=True)
    oai = OpenAI()

    block = ClarifyBlock(
        oai_client=oai,
        db_client=db_client,
    )

    async def run_ai():
        await db_client.connect()
        ans = await block.invoke(
            ids=ids,
            invoke_params={
                "task_description": "Function that returns the availability of professionals, updating based on current activity or schedule."
            },
        )
        await db_client.disconnect()
        return ans

    qna = run(run_ai())

    print(f"Thoughts: {qna.thoughts}")
    for q in qna.questions:
        print(f"\tQuestion: {q.question}")
        print(f"\tAnswer: {q.answer}")

    # If you want to test the block in an interactive environment
    import IPython

    IPython.embed()
