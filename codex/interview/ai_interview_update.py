import logging

import prisma.models

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.interview.model import UpdateUnderstanding

logger = logging.getLogger(__name__)


class InterviewUpdateBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    :param prompt_template_name: The template name for the prompt.
    :param model: The model used for processing.
    :param is_json_response: A boolean indicating if the response is in JSON format.
    :param pydantic_object: The Pydantic object associated with the block.

    Methods:
    - create_feature_list(features: list[prisma.models.Feature]): Create a list of features based on input.
    - validate(invoke_params: dict, response: ValidatedResponse) -> ValidatedResponse: Validate the response.
    - create_item(ids: Identifiers, validated_response: ValidatedResponse): Store the response in the database.
    """

    prompt_template_name = "interview/update"
    model = "gpt-4o"
    is_json_response = True
    pydantic_object = UpdateUnderstanding

    @staticmethod
    def create_feature_list(features: list[prisma.models.Feature]):
        features_section = ""
        for i, f in enumerate(features):
            features_section += f"{i}: {f.name} - {f.functionality}\n"
        return features_section

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model = UpdateUnderstanding.model_validate_json(response.response)
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
    ) -> dict[str, InterviewUpdateBlock]:
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
        feature: InterviewUpdateBlock = await feature_block.invoke(
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
    product_name: str = "'Cheese Island'"
    product_description: str = "A game based on Mokey Island but based around cheese'"
    features = "0: Storyline and Quests - Provide a humorous and engaging narrative that revolves around quests for various types of cheese and cheese-related products, mimicking the witty and adventurous spirit of Monkey Island.\n1: Puzzle Solving - Include puzzles that challenge the player to use logic, environmental clues, and cheese-related items to progress in the game.\n2: Dialogue Interactions - Craft interactive dialogues with non-player characters (NPCs) with multiple choice responses that can influence the game's outcome.\n3: Inventory System - Design an inventory system where players can collect, combine, and use cheese-related items to solve puzzles or complete quests.\n4: Visuals and Art Style - Develop distinctive, colorful graphics and an art style that reflects the playful and whimsical nature of a cheese-themed adventure.\n5: Audio and Soundtracks - Integrate a soundtrack with catchy, thematic music along with sound effects that complement the game’s cheese theme."
    user_msg = "Remove the Audio and Soundtracks and Visuals and Art Style please"
    feature_block = InterviewUpdateBlock()

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
