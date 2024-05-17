import logging

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.interview.model import UndestandRequest

logger = logging.getLogger(__name__)


class InterviewBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    prompt_template_name = "interview/understand"
    model = "gpt-4o"
    is_json_response = True
    pydantic_object = UndestandRequest

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = UndestandRequest.model_validate_json(response.response)
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
    import asyncio

    import prisma
    from openai import AsyncOpenAI

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.test_const import identifier_1

    class Colors:
        USER = "\033[94m"
        CODEX = "\033[92m"
        END = "\033[0m"

    async def run_ai(
        product_name, product_description, features, user_msg
    ) -> dict[str, InterviewBlock]:
        await db_client.connect()
        if not ids.user_id:
            raise AssertionError("User ID not found")
        app = await prisma.models.Application.prisma().create(
            data={
                "name": product_name,
                "description": product_description,
                "User": {"connect": {"id": ids.user_id}},
            }
        )
        ids.app_id = app.id
        feature: InterviewBlock = await feature_block.invoke(
            ids=ids,
            invoke_params={
                "product_name": product_name,
                "product_description": product_description,
                "features": features,
                "user_msg": user_msg,
            },
        )
        await db_client.disconnect()
        return {"features": feature}

    def print_output(features, user_msg=None):
        output = ""
        if user_msg:
            output += f"\n\n{Colors.USER}User: {user_msg}{Colors.END}\n\n"

        output += f"App Name: {product_name}, Completed: {features['features'].phase_completed}\n\n"
        output += (
            f"{Colors.CODEX}Codex: {features['features'].say_to_user}{Colors.END}\n\n"
        )
        output += "Thoughts: " + str(features["features"].thoughts)
        if features["features"].features:
            output += "\nFeatures:\n\n"
            for feature in features["features"].features:
                output += "\nFeature Name: " + str(feature.name)
                output += "\nFunctionality: " + str(feature.functionality)
                output += "\nReasoning: " + str(feature.reasoning)
                output += "\n"
        print(output)

    OpenAIChatClient.configure(openai_config={})
    ids = identifier_1
    db_client = prisma.Prisma(auto_register=True)
    oai = AsyncOpenAI()
    product_name: str = "'Tutor App'"
    product_description: str = "The Tutor App is an application designed to help tutors manage their tutoring business and clients manage their tutoring sessions. The key users are both tutors and clients. Tutors need features to set availability, manage clients, schedule sessions, send invoices and track payments. Clients need to find tutors, book and manage appointments, communicate with tutors, and pay invoices. Core features like user accounts, authentication, notifications span both groups. But the functionality aims to let tutors run their services smoothly while giving clients control over their tutoring.'"
    features = None
    user_msg = None
    feature_block = InterviewBlock()

    features = asyncio.run(
        run_ai(product_name, product_description, features, user_msg)
    )
    logger.info(features)
    print_output(features)

    user_msg = "I want to be able to create my own AI tutor as well"
    features = asyncio.run(
        run_ai(product_name, product_description, features, user_msg)
    )
    print_output(features, user_msg)

    user_msg = "Thats great thank you, please build it."
    features = asyncio.run(
        run_ai(product_name, product_description, features, user_msg)
    )
    print_output(features, user_msg)
