import logging

from codex.api_model import DatabaseEnums, DatabaseSchema, DatabaseTable
from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.ai_model import OpenAIChatClient
from codex.common.exec_external_tool import OutputType, exec_external_on_contents
from codex.common.logging_config import setup_logging
from codex.common.parse_prisma import parse_prisma_schema
from codex.requirements.model import DBResponse, PreAnswer

logger = logging.getLogger(__name__)

PRISMA_FILE_HEADER = """
// datasource db defines the database connection settings.
// It is configured for PostgreSQL and uses an environment variable for the connection URL.
// The 'extensions' feature enables the use of PostgreSQL-specific data types.
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
}

// generator db configures Prisma Client settings.
// It is set up to use Prisma Client Python with asyncio interface and specific features.
generator db {
  provider             = "prisma-client-py"
  interface            = "asyncio"
  recursive_type_depth = 5
  previewFeatures      = ["postgresqlExtensions"]
}

"""


def extract_prisma_errors(error_message: str) -> set[str]:
    """
    Extracts the error messages from the prisma output
    """

    split_text = error_message.split("[1;91merror[0m: \x1b[1m")

    # Extract error messages by taking the portion up to the next reset ANSI code sequence
    errors = [
        part.split("[0m")[0] for part in split_text[1:]
    ]  # Skip the first split as it's before the first error

    return set(errors)


class DatabaseGenerationBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/database"
    # Model to use for the LLM
    model = "gpt-4o"
    # Should we force the LLM to reply in JSON
    is_json_response = False
    # If we are using is_json_response, what is the response model

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        validation_errors = set()
        logger.warning(f"Validating response:\n{response.response}")
        text_schema = ""
        try:
            schema_blocks = response.response.split("```prisma")
            schema_blocks.pop(0)
            if len(schema_blocks) != 1:
                if len(schema_blocks) == 0:
                    # If there are no prisma blocks, then check for plain code blocks
                    schema_blocks = response.response.split("```")
                    if len(schema_blocks) != 3:
                        raise ValidationError(
                            "No ```prisma blocks found in the response. Make your code block start with ```prisma"
                        )
                    else:
                        text_schema = schema_blocks[1]
            else:
                text_schema = schema_blocks[0].split("```")[0]
        except Exception as e:
            raise ValidationError(f"Error parsing the response: {e}")

        if "datasource db {" not in text_schema:
            unparsed = PRISMA_FILE_HEADER + text_schema
        else:
            unparsed = text_schema
        try:
            unparsed = await exec_external_on_contents(
                ["prisma", "format", "--schema"],
                unparsed,
                output_type=OutputType.STD_ERR,
            )
        except ValidationError as e:
            validation_errors = validation_errors.union(extract_prisma_errors(str(e)))

        try:
            unparsed = await exec_external_on_contents(
                ["prisma", "validate", "--schema"],
                unparsed,
                output_type=OutputType.STD_ERR,
            )
        except ValidationError as e:
            validation_errors = validation_errors.union(extract_prisma_errors(str(e)))

        parsed_prisma = parse_prisma_schema(unparsed)

        if validation_errors:
            raise ValidationError("\n- ".join(validation_errors))

        enums_objs = []
        for name, details in parsed_prisma.enums.items():
            enums_objs.append(
                DatabaseEnums(
                    name=name,
                    values=details.values,
                    description="",
                    definition=details.definition,
                )
            )

        table_objs = []
        for name, details in parsed_prisma.models.items():
            table_objs.append(
                DatabaseTable(
                    name=name,
                    definition=details.definition,
                    description="",
                )
            )

        response.response = DBResponse(
            think="",
            anti_think="",
            plan="",
            refine="",
            pre_answer=PreAnswer(tables=[], enums=[]),
            pre_answer_issues="",
            full_schema="",
            database_schema=DatabaseSchema(
                name="Database Schema",
                description="The schema for the applications database",
                enums=enums_objs,
                tables=table_objs,
            ),
            conclusions="",
        )

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
    import json
    import os
    from asyncio import run

    import prisma

    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging()

    OpenAIChatClient.configure({})
    db_client = prisma.Prisma(auto_register=True)
    logging.info("Running block")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(current_dir, "ai_database_test_data.json")

    with open(test_file, "r") as file:
        invoke_params = json.load(file)
    # This is the input to the block

    database_block = DatabaseGenerationBlock()

    async def run_ai() -> dict[str, DBResponse]:
        await db_client.connect()

        app = await prisma.models.Application.prisma().find_first(
            where={"id": ids.app_id},  # type: ignore
        )
        if not app:
            await prisma.models.Application.prisma().create(
                data={
                    "id": ids.app_id,  # type: ignore
                    "name": "Test Application",
                    "description": "This is a test application",
                }
            )

        database: DBResponse = await database_block.invoke(
            ids=ids,
            invoke_params=invoke_params,
        )

        await db_client.disconnect()
        return {
            "database": database,
        }

    modules = run(run_ai())

    prisma_file = PRISMA_FILE_HEADER

    logger.info("Database Generation Block Response")

    for key, item in modules.items():
        if isinstance(item, DBResponse):
            logger.info(f"ModuleResponse {key}")
            logger.info(f"\tThought General: {item.think}")
            logger.info(f"\tThought Anti: {item.anti_think}")
            logger.info(f"\tPlan: {item.plan}")
            logger.info(f"\tRefine: {item.refine}")
            logger.info(f"\tPre Answer: {item.pre_answer}")
            logger.info(f"\tPre Answer Issues: {item.pre_answer_issues}")
            logger.info(f"\tFull Schema: {item.full_schema}")
            logger.info(f"\tConclusions: {item.conclusions}")

            enums: list[DatabaseEnums] = item.database_schema.enums
            for e in enums:
                prisma_file += e.definition
                prisma_file += "\n\n"
                logger.info(f"\t\tEnum Name: {e.name}")
                logger.info(f"\t\tEnum Values: {e.values}")
                logger.info(f"\t\tEnum Description: {e.description}")
                logger.info(f"\t\tEnum Definition: {e.definition}")
            tables: list[DatabaseTable] = item.database_schema.tables
            for t in tables:
                prisma_file += t.definition
                prisma_file += "\n\n"
                logger.info(f"\t\tTable Name: {t.name}")
                logger.info(f"\t\tTable Definition: {t.definition}")
                logger.info(f"\t\tTable Description: {t.description}")
            logger.warning(f"Prisma File:\n{prisma_file}")
        else:
            logger.info("????")

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
