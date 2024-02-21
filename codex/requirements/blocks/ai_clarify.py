import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.logging_config import setup_logging
from codex.requirements.model import Clarification, QandA, QandAResponses

logger = logging.getLogger(__name__)


class FrontendClarificationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/clarifications/frontend"
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
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass


class UserPersonaClarificationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user
    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/clarifications/user_persona"
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
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass


class UserSkillClarificationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user
    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/clarifications/user_skill"
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
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass


class QuestionAndAnswerClarificationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user
    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/clarifications/q_and_a"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = QandAResponses

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = QandAResponses.model_validate_json(response.response)

            q_and_a: list[QandA] = []
            for wrapped in model.answer:
                converted_q_and_a = wrapped.wrapper
                q_and_a.append(converted_q_and_a)

            response.response = q_and_a

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

    from openai import AsyncOpenAI
    from prisma import Prisma

    from codex.common.test_const import identifier_1

    ids = identifier_1
    db_client = Prisma(auto_register=True)
    oai = AsyncOpenAI()

    task: str = "Write a function to return the availability of a professional from their calendar"
    project_description: str = "Function that returns the availability of professionals, updating based on current activity or schedule."

    frontend_block = FrontendClarificationBlock(
        oai_client=oai,
    )
    user_persona_block = UserPersonaClarificationBlock(oai_client=oai)
    user_skill_block = UserSkillClarificationBlock(oai_client=oai)
    q_and_a_block = QuestionAndAnswerClarificationBlock(oai_client=oai)

    async def run_ai() -> dict[str, list[QandA] | Clarification]:
        await db_client.connect()
        frontend: Clarification = await frontend_block.invoke(
            ids=ids,
            invoke_params={"project_description": project_description},
        )
        user_persona: Clarification = await user_persona_block.invoke(
            ids=ids,
            invoke_params={
                "clarifiying_questions_so_far": "- Do we need a frontend: Yes",
                "project_description": project_description,
            },
        )
        user_skill: Clarification = await user_skill_block.invoke(
            ids=ids,
            invoke_params={
                "clarifiying_questions_so_far": "- Do we need a frontend: Yes\n- Who is the expected user: Frontline staff scheduling appointments, professionals managing their schedules, and individuals seeking appointments.",
                "project_description": project_description,
            },
        )
        q_and_a: list[QandA] = await q_and_a_block.invoke(
            ids=ids,
            invoke_params={
                "clarifiying_questions_so_far": "- Do we need a frontend: Yes\n- Who is the expected user: Frontline staff scheduling appointments, professionals managing their schedules, and individuals seeking appointments.",
                "project_description": project_description,
                "task": task,
            },
        )

        await db_client.disconnect()
        return {
            "frontend": frontend,
            "user_persona": user_persona,
            "user_skill": user_skill,
            "QAndA": q_and_a,
        }

    qna = run(run_ai())

    for key, clariifcation in qna.items():
        if isinstance(clariifcation, Clarification):
            logger.info(f"Clarification {key}")
            logger.info(f"\tThoughts: {clariifcation.thoughts}")
            logger.info(f"\tQuestion: {clariifcation.question}")
            logger.info(f"\tAnswer: {clariifcation.answer}")
        elif isinstance(clariifcation, list):
            for qa in clariifcation:
                logger.info(f"Q and A")
                logger.info(f"\tQuestion: {qa.question}")
                logger.info(f"\tThoughts: {qa.thoughts}")
                logger.info(f"\tConclusive: {qa.was_conclusive}")
                logger.info(f"\tAnswer: {qa.team_answer}")

        else:
            logger.info(f"????")

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
