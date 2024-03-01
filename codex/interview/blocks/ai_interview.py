import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.interview.model import InterviewMessageUse

logger = logging.getLogger(__name__)


class InterviewBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/interview/interview_agent"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = InterviewMessageUse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: InterviewMessageUse = InterviewMessageUse.model_validate_json(
                response.response, strict=False
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

    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging(local=True)

    OpenAIChatClient.configure({})
    db_client = Prisma(auto_register=True)

    interview_block = InterviewBlock()

    async def run_ai() -> dict[str, InterviewMessageUse]:
        await db_client.connect()
        response_ref: InterviewMessageUse = await interview_block.invoke(
            ids=ids,
            invoke_params={
                "task": """The Tutor App is an app designed for tutors to manage their clients,
 schedules, and invoices.

It must support both the client and tutor scheduling, rescheduling and canceling
 appointments, and sending invoices after the appointment has passed.

Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign
 up with traditional authentication, it must be safe and secure. There will need to be
 password reset and login capabilities.

There will need to be authorization for identifying clients vs the tutor.

Additionally, it will have proper management of financials, including invoice management
 and payment tracking. This includes things like paid/failed invoice notifications,
 unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.""",
                "tools": {
                    "ask": "ask the user a question",
                    "search": "search the web for information",
                    "finished": "finish the task and provide a comprehensive project to the user. Include the important notes from the task as well. This should be very detailed and comprehensive. Do NOT use this if there are unsettled questions.",
                },
                "memory": [],
                "tech_stack": {
                    "programming_language": "Python",
                    "api_framework": "FastAPI",
                    "frontend_framework": "React",
                    "database": "PostgreSQL",
                    "orm": "Prisma",
                },
            },
        )

        response_with_memory: InterviewMessageUse = await interview_block.invoke(
            ids=ids,
            invoke_params={
                "task": """The Tutor App is an app designed for tutors to manage their clients,
 schedules, and invoices.

It must support both the client and tutor scheduling, rescheduling and canceling
 appointments, and sending invoices after the appointment has passed.

Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign
 up with traditional authentication, it must be safe and secure. There will need to be
 password reset and login capabilities.

There will need to be authorization for identifying clients vs the tutor.

Additionally, it will have proper management of financials, including invoice management
 and payment tracking. This includes things like paid/failed invoice notifications,
 unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.""",
                "tools": {
                    "ask": "ask the user a question",
                    "search": "search the web for information",
                    "finished": "finish the task and provide a comprehensive project to the user. Include the important notes from the task as well. This should be very detailed and comprehensive. Do NOT use this if there are unsettled questions.",
                },
                "tech_stack": {
                    "programming_language": "Python",
                    "api_framework": "FastAPI",
                    "frontend_framework": "React",
                    "database": "PostgreSQL",
                    "orm": "Prisma",
                },
                "memory": [
                    {
                        "tool": "ask",
                        "content": "How do you currently manage your tutoring appointments and invoices?",
                        "response": "I currently use a combination of Google Calendar and a spreadsheet to manage my tutoring appointments and invoices. I manually create appointments in Google Calendar and then manually create invoices in a spreadsheet. It is a very manual process and I am looking for a more automated solution.",
                    },
                    {
                        "tool": "ask",
                        "content": "How important is the feature of scheduling, rescheduling, and canceling appointments for you?",
                        "response": "Scheduling, rescheduling, and canceling appointments is very important for me. I have a very busy schedule and need to be able to easily manage my appointments.",
                    },
                    {
                        "tool": "ask",
                        "content": "Do you prefer signing up with OAuth2 providers or traditional sign-in methods for your applications?",
                        "response": "I prefer signing up with OAuth2 providers. It is more convenient and secure. However, I also need the option for traditional sign-in methods for users who do not want to use OAuth2.",
                    },
                    {
                        "tool": "ask",
                        "content": "What security measures do you expect for traditional sign-in methods?",
                        "response": "For traditional sign-in methods, I expect strong password requirements, secure password storage, and the ability to reset passwords if needed.",
                    },
                    {
                        "tool": "ask",
                        "content": "How do you distinguish between clients and tutors in your current system?",
                        "response": "In my current system, I am the only tutor, so I do not need to distinguish between clients and tutors. However, in the future, I may need to be able to distinguish between clients and tutors.",
                    },
                    {
                        "tool": "ask",
                        "content": "How important is financial management, such as invoice management and payment tracking, in your tutoring activities?",
                        "response": "Financial management is very important to me. I need to be able to easily create and send invoices, track payments, and generate reports on my tutoring income.",
                    },
                    {
                        "tool": "ask",
                        "content": "Do you need detailed reports on your tutoring income, and how often do you usually review these reports?",
                        "response": "I need detailed reports on my tutoring income, including paid/failed invoice notifications, unpaid invoice follow-up, and summarizing d/w/m/y income. I review these reports monthly.",
                    },
                    {
                        "tool": "search",
                        "content": "best practices for implementing OAuth2 in mobile applications",
                        "response": "Best practices for implementing OAuth2 in mobile applications include using secure and well-maintained libraries, following the OAuth2 specification, and using secure token storage and transmission.",
                    },
                    {
                        "tool": "search",
                        "content": "secure password storage and reset methodologies",
                        "response": "Secure password storage and reset methodologies include using strong hashing algorithms, salting passwords, and implementing multi-factor authentication. Password reset methodologies include using secure token-based reset links and requiring additional verification before resetting a password.",
                    },
                    {
                        "tool": "search",
                        "content": "financial management tools for freelancers",
                        "response": "Financial management tools for freelancers include FreshBooks, QuickBooks Self-Employed, and Wave. These tools can help freelancers create and send invoices, track payments, and generate reports on their income.",
                    },
                ],
            },
        )

        await db_client.disconnect()
        return {
            "response_ref": response_ref,
            "response_with_memory": response_with_memory,
        }

    responses = run(run_ai())

    for key, item in responses.items():
        if isinstance(item, InterviewMessageUse):
            logger.info(f"{key}:")
            for message in item.uses:
                logger.info(f"\t{message.tool}: {message.content}")
        else:
            logger.info(f"????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
