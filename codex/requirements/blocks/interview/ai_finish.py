from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.requirements.model import InterviewMessageWithResponse


class FinishBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/interview/finish"
    # Model to use for the LLM
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = InterviewMessageWithResponse

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: InterviewMessageWithResponse = (
                InterviewMessageWithResponse.model_validate_json(response.response)
            )
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

    ids = Indentifiers(user_id=1, app_id=1)
    db_client = Prisma(auto_register=True)
    oai = OpenAI()

    finish_block = FinishBlock(
        oai_client=oai,
    )

    async def run_ai() -> dict[str, InterviewMessageWithResponse]:
        await db_client.connect()
        memory: list[InterviewMessageWithResponse] = [
            InterviewMessageWithResponse(
                tool="ask",
                content="How do you currently manage your tutoring appointments and invoices?",
                response="I currently use a combination of Google Calendar and a spreadsheet to manage my tutoring appointments and invoices. I manually create appointments in Google Calendar and then manually create invoices in a spreadsheet. It is a very manual process and I am looking for a more automated solution.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="Do you prefer signing up with OAuth2 providers or traditional sign-in methods for your applications?",
                response="I prefer signing up with OAuth2 providers. It is more convenient and secure. However, I also need the option for traditional sign-in methods for users who do not want to use OAuth2.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="What security measures do you expect for traditional sign-in methods?",
                response="For traditional sign-in methods, I expect strong password requirements, secure password storage, and the ability to reset passwords if needed.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="How do you distinguish between clients and tutors in your current system?",
                response="In my current system, I am the only tutor, so I do not need to distinguish between clients and tutors. However, in the future, I may need to be able to distinguish between clients and tutors.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="How important is financial management, such as invoice management and payment tracking, in your tutoring activities?",
                response="Financial management is very important to me. I need to be able to easily create and send invoices, track payments, and generate reports on my tutoring income.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="Do you need detailed reports on your tutoring income, and how often do you usually review these reports?",
                response="I need detailed reports on my tutoring income, including paid/failed invoice notifications, unpaid invoice follow-up, and summarizing d/w/m/y income. I review these reports monthly.",
            ),
            InterviewMessageWithResponse(
                tool="search",
                content="best practices for implementing OAuth2 in mobile applications",
                response="Best practices for implementing OAuth2 in mobile applications include using secure and well-maintained libraries, following the OAuth2 specification, and using secure token storage and transmission.",
            ),
            InterviewMessageWithResponse(
                tool="search",
                content="secure password storage and reset methodologies",
                response="Secure password storage and reset methodologies include using strong hashing algorithms, salting passwords, and implementing multi-factor authentication. Password reset methodologies include using secure token-based reset links and requiring additional verification before resetting a password.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="How important is the feature of scheduling, rescheduling, and canceling appointments for you?",
                response="Scheduling, rescheduling, and canceling appointments is very important for me. I have a very busy schedule and need to be able to easily manage my appointments.",
            ),
            InterviewMessageWithResponse(
                tool="ask",
                content="Do you need the ability to set up recurring appointments?",
                response="Yes, I need the ability to set up recurring appointments. I have many clients who have regular tutoring sessions with me.",
            ),
            InterviewMessageWithResponse(
                tool="search",
                content="Financial management tools for freelancers",
                response="Financial management tools for freelancers include FreshBooks, QuickBooks Self-Employed, and Wave. These tools can help freelancers create and send invoices, track payments, and generate reports on their income.",
            ),
        ]

        content = """The Tutor App is designed to streamline the management process for tutors in handling their client engagements, schedules, and financial transactions. The primary functionalities outlined for implementation include a robust appointment system that supports scheduling, rescheduling, and canceling appointments, which is vital for managing a busy tutoring schedule. Following an appointment, the system will automatically manage invoicing, sending detailed invoices to clients reflecting the session's conclusion.

To accommodate various user preferences, the app will offer dual signup options: OAuth2 for users seeking a convenient and secure single sign-on experience, and traditional sign-in methods for those desiring or necessitating an alternative. Essential to the traditional sign-in method is the implementation of contemporary security practices, including stringent password requirements, secure hash-based storage, and a user-friendly password reset mechanism.

Authorization features within the app will distinctly identify clients and the tutor, safeguarding against unauthorized access and ensuring a tailored user experience for both parties. Enhanced financial management tools are also a cornerstone of the app’s design, encompassing comprehensive invoice management and payment tracking functionalities. These will facilitate immediate feedback on payment statuses, efficient follow-up on outstanding invoices, and the generation of detailed financial reports spanning daily, weekly, monthly, and yearly overviews.

Informed by discussions around user needs and industry best practices, the app will incorporate secure password storage methodologies, leveraging strong hashing algorithms and multi-factor authentication where necessary. This aligns with the expressed need for high data security, especially in conventional authentication contexts.

OAuth2 integration will follow acknowledged best practices, emphasizing the secure handling of tokens and the utilization of reliable libraries to ensure the integrity of this authentication pathway.

The financial management aspect, a critical component, will be designed to emulate the functionalities of successful freelancing tools, providing intuitive and comprehensive management of tutoring income and expenses. This portion of the app will offer detailed insights and reminders to support tutors in maintaining a clear view of their business's financial health.

In summary, The Tutor App aims to offer a comprehensive solution to the administrative challenges faced by tutors, emphasizing ease of use, security, and efficient management of appointments and finances."""

        response_ref: InterviewMessageWithResponse = await finish_block.invoke(
            ids=ids,
            invoke_params={
                "content": content,
                "memory": memory,
            },
        )

        await db_client.disconnect()
        return {
            "response_ref": response_ref,
        }

    responses = run(run_ai())

    for key, item in responses.items():
        if isinstance(item, InterviewMessageWithResponse):
            print(f"\t{item.tool}: {item.content}: {item.response}")
        else:
            print(f"????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
