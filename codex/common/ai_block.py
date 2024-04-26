import glob
import hashlib
import logging
import os
import pathlib
import typing
from typing import Any, Callable, Optional, Type

import prisma
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from prisma.enums import DevelopmentPhase
from prisma.fields import Json
from prisma.models import LLMCallAttempt, LLMCallTemplate
from pydantic import BaseModel, ConfigDict

from codex.api_model import Identifiers
from codex.common.ai_model import OpenAIChatClient

load_dotenv()
logger = logging.getLogger(__name__)

from openai import AsyncOpenAI  # noqa
from openai.types import CompletionUsage  # noqa
from openai.types.chat import ChatCompletion  # noqa


class LLMFailure(Exception):
    pass


class ParsingError(Exception):
    pass


class ErrorEnhancements(BaseModel):
    metadata: typing.Optional[str]
    context: typing.Optional[str]
    suggested_fix: typing.Optional[str] = None


class ValidationError(Exception):
    enhancements: Optional[ErrorEnhancements] = None

    def __init__(self, error: str, enhancements: Optional[ErrorEnhancements] = None):
        super().__init__(error)
        self.enhancements = enhancements


class ValidationErrorWithContent(ValidationError):
    content: str

    def __init__(
        self, error: str, content: str, enhancements: Optional[ErrorEnhancements] = None
    ):
        super().__init__(error=error, enhancements=enhancements)
        self.content = content


class LineValidationError(ValidationError):
    line_from: int
    line_to: int
    code: str

    def __init__(
        self,
        error: str,
        code: str,
        line_from: int,
        line_to: int | None = None,
        enhancements: Optional[ErrorEnhancements] = None,
    ):
        super().__init__(error=error, enhancements=enhancements)
        self.line_from = line_from
        self.line_to = line_to if line_to else line_from + 1
        self.code = code

    def __parse_line_code(self) -> str:
        lines = self.code.split("\n")
        if self.line_from > len(lines):
            return ""
        return "\n".join(lines[self.line_from - 1 : self.line_to - 1])

    def __str__(self):
        return f"{super().__str__()} -> '{self.__parse_line_code()}'"


class ListValidationError(ValidationError):
    errors: list[ValidationError]

    def __init__(self, message: str, errors: list[ValidationError] | None = None):
        super().__init__(message)
        self.errors = errors if errors else []

    def __str__(self):
        errors = ["\n  - " + "   \n".join(e.__str__().split("\n")) for e in self.errors]
        return f"{super().__str__()}{''.join(errors)}".strip()

    def append_error(self, error: ValidationError):
        self.errors.append(error)

    def append_message(self, message: str):
        self.errors.append(ValidationError(message))

    def raise_if_errors(self):
        if self.errors:
            raise self


class PromptTemplateInvocationError(Exception):
    pass


class ValidatedResponse(BaseModel):
    response: Any
    usage_statistics: CompletionUsage
    message: str

    class config:
        arbitrary_types_allowed = True


# This can be used for synchronous testing without making an actual API call
MOCK_RESPONSE = ""


class AIBlock:
    """
    The AI BLock is a base class for all AI Blocks. It provides a common interface for
    calling an LLM, parsing the response, validating the response, and then storing it
    along with the call attempt in the database.

    It also holds the database call logic for creating, updating, getting, and deleting
    objects generated from the AI Block.

    YOU MUST IMPLEMENT THE FOLLOWING METHODS:
        - def validate(
            self,
            invoke_params: dict,
            response: ValidatedResponse
            ) -> ValidatedResponse:
        - async def create_item(self, validated_response: ValidatedResponse):

    You should also implement theses methods if you want to use the database logic:
        - async def update_item(self, query_params: dict):
        - async def get_item(self, query_params: dict):
        - async def delete_item(self, query_params: dict):
        - async def list_items(self, query_params: dict):
    """

    developement_phase = DevelopmentPhase.REQUIREMENTS
    prompt_template_name = ""
    language = None
    model = ""
    is_json_response = False
    pydantic_object = None
    template_base_path = "prompts"

    def __init__(
        self,
    ):
        """
        Args:
            oai_client (AsyncOpenAI): The OpenAI client
            db_client (Prisma): The Prisma Database client
        """
        self.oai_client = OpenAIChatClient.get_instance()
        self.template_base_path_with_model = pathlib.Path(
            os.path.join(
                os.path.dirname(__file__),
                f"../{self.template_base_path}/{self.model}",
            )
        ).resolve(strict=True)
        self.templates_dir = self.template_base_path_with_model
        self.call_template_id = None
        self.load_pydantic_format_instructions()
        self.verbose: bool = os.getenv("VERBOSE_LOGGING", "true").lower() in (
            "true",
            "1",
            "t",
        )

    def load_pydantic_format_instructions(self):
        if self.pydantic_object:
            schema = self.pydantic_object.schema_json()

            template_dir = os.path.join(
                os.path.dirname(__file__),
                "../prompts/techniques/",
            )
            try:
                templates_env = Environment(loader=FileSystemLoader(template_dir))
                prompt_template = templates_env.get_template(
                    "pydantic_format_instruction.j2"
                )
                self.PYDANTIC_FORMAT_INSTRUCTIONS = prompt_template.render(
                    {"schema": schema}
                )
            except Exception as e:
                logger.error(f"Error loading template: {e}")
                raise PromptTemplateInvocationError(f"Error loading template: {e}")

    async def store_call_template(self):
        """
        Stores the call template in the database.

        Returns:
            call_template (LLMCallTemplate): The stored call template object.
        """
        lang_str = ""
        if self.language:
            lang_str = f"{self.language}."

        prompts = {"system": "", "user": "", "retry": ""}

        for key in ["system", "user", "retry"]:
            # Pattern to match the files
            pattern = (
                f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}{key}*.j2"
            )

            files = glob.glob(pattern)
            for file_path in files:
                # Reading and appending file name and contents

                relative_file_path = os.path.relpath(
                    file_path, self.template_base_path_with_model
                )
                with open(file_path, "r") as file:
                    contents = file.read()

                    prompts[key] += f"\n{relative_file_path}:\n{contents}\n"

        all_prompts_combined = "".join(prompts.values())
        self.template_hash = hashlib.md5(all_prompts_combined.encode()).hexdigest()

        # Check if an entry with the same fileHash already exists
        existing_template = await LLMCallTemplate.prisma().find_first(
            where={
                "fileHash": self.template_hash,
            }
        )

        # If an existing entry is found, use it instead of creating a new one
        if existing_template:
            call_template = existing_template
        else:
            # If no entry exists with the same fileHash, create a new one
            call_template = await LLMCallTemplate.prisma().create(
                data={
                    "templateName": self.prompt_template_name,
                    "fileHash": self.template_hash,
                    "model": self.model,
                    "systemPrompt": prompts["system"],
                    "userPrompt": prompts["user"],
                    "retryPrompt": prompts["retry"],
                    "developmentPhase": self.developement_phase,
                }
            )

        # Store the call template ID for future use
        self.call_template_id = call_template.id

        return call_template

    async def store_call_attempt(
        self,
        ids: Identifiers,
        response: ValidatedResponse,
        attempt: int,
        prompt: Json,
        first_call_id: str | None = None,
    ):
        if not self.call_template_id:
            raise AssertionError("Call template ID not set")

        data = prisma.types.LLMCallAttemptCreateInput(
            model=self.model,
            completionTokens=response.usage_statistics.completion_tokens,
            promptTokens=response.usage_statistics.prompt_tokens,
            totalTokens=response.usage_statistics.total_tokens,
            attempt=attempt,
            prompt=prompt,
            response=response.message,
            LLMCallTemplate={"connect": {"id": self.call_template_id}},
        )

        data.update(
            {
                table: {"connect": {"id": id}}
                for table, id in [
                    ("User", ids.user_id),
                    ("Application", ids.app_id),
                    ("CompiledRoute", ids.compiled_route_id),
                    ("Function", ids.function_id),
                    ("CompletedApp", ids.completed_app_id),
                    ("Deployment", ids.deployment_id),
                    ("FirstCall", first_call_id),
                ]
                if id
            }
        )

        call_attempt = await LLMCallAttempt.prisma().create(data=data)
        return call_attempt

    def load_template(self, template: str, invoke_params: dict) -> str:
        try:
            lang_str = ""
            if self.language:
                lang_str = f"{self.language}."
            templates_env = Environment(loader=FileSystemLoader(self.templates_dir))
            prompt_template = templates_env.get_template(
                f"{self.prompt_template_name}/{lang_str}{template}.j2"
            )
            return prompt_template.render(**invoke_params)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            raise PromptTemplateInvocationError(f"Error loading template: {e}")

    @staticmethod
    def messages_to_prompt_string(messages: list) -> str:
        prompt = ""
        for message in messages:
            prompt += f"### {message['role']}\n\n {message['content']}\n\n"
        return prompt

    def parse(self, response: ChatCompletion) -> ValidatedResponse:
        usage_statistics = response.usage
        message = response.choices[0].message

        if message.tool_calls is not None:
            raise NotImplementedError("Tool calls are not supported")
        elif message.function_call is not None:
            raise NotImplementedError("Function calls are not supported")

        if usage_statistics is None:
            raise ParsingError("Usage statistics are missing")

        if message.content is None:
            raise ParsingError("Message content is missing")

        return ValidatedResponse(
            response=message.content,
            usage_statistics=usage_statistics,
            message=message.content,
        )

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        Validates the generated resposne is correct
        Args:
            invoke_params (dict): the invole parameters for ths call
            response (ValidatedResponse): the parsed response

        Returns:
            ValidatedResponse: the validated response

        Raises:
            ValidationError: if the response is invalid
        """
        raise NotImplementedError("Validate Method not implemented")

    def get_format_instructions(self) -> str:
        if not self.pydantic_object:
            raise ValueError("pydantic_object not set")

        return self.PYDANTIC_FORMAT_INSTRUCTIONS

    async def invoke(self, ids: Identifiers, invoke_params: dict, max_retries=5) -> Any:
        if ids.user_id is None:
            raise ValueError("User ID not set")
        if ids.app_id is None:
            raise ValueError("App ID not set")
        validated_response = None
        if not self.call_template_id:
            await self.store_call_template()
        presponse = None
        retry_attempt = 0
        first_llm_call_id = None
        try:
            invoke_params["will_retry_on_failure"] = True
            if self.is_json_response:
                invoke_params["format_instructions"] = self.get_format_instructions()
            system_prompt = self.load_template("system", invoke_params)
            user_prompt = self.load_template("user", invoke_params)

            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 4095,
            }

            if self.is_json_response:
                request_params["response_format"] = {"type": "json_object"}
        except Exception as e:
            logger.error(f"Error creating request params: {e}")
            raise LLMFailure(f"Error creating request params: {e}")
        try:
            presponse = await self.call_llm(request_params)

            first_llm_call_id = (
                await self.store_call_attempt(
                    ids,
                    presponse,
                    retry_attempt,
                    Json(request_params["messages"]),
                )
            ).id

            # Increment it here so the first retry is 1
            retry_attempt += 1
            invoke_params["will_retry_on_failure"] = retry_attempt < max_retries

            validated_response = await self.validate(invoke_params, presponse)
        except ValidationError as validation_error:
            logger.error(
                f"Failed initial generation attempt: {validation_error}, LLM Call ID: {first_llm_call_id}"
            )
            error_message = validation_error
            while retry_attempt <= max_retries:
                try:
                    if presponse:
                        invoke_params["generation"] = presponse.message
                    else:
                        invoke_params["generation"] = "Error generating response"
                    invoke_params["error"] = str(error_message)

                    # Collect the enhancements from all the errors
                    all_enhancements: list[ErrorEnhancements] = []
                    if isinstance(error_message, ListValidationError):
                        all_enhancements = [
                            error_message.enhancements
                            for error_message in error_message.errors
                            if error_message.enhancements
                        ]
                    elif error_message.enhancements:
                        all_enhancements = [error_message.enhancements]
                    invoke_params["enhancements"] = all_enhancements

                    retry_prompt = self.load_template("retry", invoke_params)
                    request_params["messages"] = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt},
                    ]
                    presponse = await self.call_llm(request_params)
                    if not request_params["messages"]:
                        raise AssertionError("Messages not set")

                    await self.store_call_attempt(
                        ids,
                        presponse,
                        retry_attempt,
                        Json(request_params["messages"]),
                        first_llm_call_id,
                    )
                    validated_response = await self.validate(invoke_params, presponse)
                    break
                except ValidationError as retry_error:
                    logger.error(
                        f"{retry_attempt}/{max_retries}"
                        f" [{self.prompt_template_name}] Failed validating response: {retry_error}"
                        f" LLM Call ID: {first_llm_call_id} - retry attempt #{retry_attempt}"
                    )
                    error_message = retry_error
                    retry_attempt += 1
                    invoke_params["will_retry_on_failure"] = retry_attempt < max_retries
                    continue
            if not validated_response:
                await self.on_failed(ids, invoke_params)
                raise LLMFailure(f"Error validating response: {validation_error}")
        except Exception as unkown_error:
            logger.exception(f"Error invoking AIBlock: {unkown_error}", unkown_error)
            raise LLMFailure(f"Error invoking AIBlock: {unkown_error}")

        stored_obj = await self.create_item(ids, validated_response)
        return stored_obj if stored_obj else validated_response.response

    async def call_llm(self, request_params: dict) -> ValidatedResponse:
        if MOCK_RESPONSE:
            return ValidatedResponse(
                response=MOCK_RESPONSE,
                usage_statistics=CompletionUsage(
                    completion_tokens=0, prompt_tokens=0, total_tokens=0
                ),
                message=MOCK_RESPONSE,
            )

        if self.verbose:
            logger.info(
                f"📤 Calling LLM {request_params['model']} with the following input:\n {request_params['messages']}"
            )
        response = await self.oai_client.chat(request_params)
        if self.verbose and response:
            logger.info(f"📥 LLM response: {response}")
        return self.parse(response)

    async def on_failed(self, ids: Identifiers, invoke_params: dict):
        """
        Called when the LLM call fails

        Args:
            ids (Identifiers): The identifiers for the call
            invoke_params (dict): The invoke parameters
        """
        # We just pass here as we want implementing this to be optional

        logger.error(
            f"Failed to generate response for {self.prompt_template_name}",
            extra=ids.model_dump(),
        )
        pass

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        Create an item from the validated response

        Args:
            validated_response (ValidatedResponse): _description_
        """
        raise NotImplementedError("Create Item Method not implemented")

    async def update_item(self, query_params: dict):
        """
        Update an existing item in the database

        Args:
            query_params (dict): _description_
        """
        raise NotImplementedError("Update Method not implemented")

    async def get_item(self, query_params: dict):
        """
        Gets an item from the database

        Args:
            query_params (dict): _description_
        """
        raise NotImplementedError("Get Item Method not implemented")

    async def delete_item(self, query_params: dict):
        """
        Deletes an item from the database

        Args:
            query_params (dict): _description_
        """
        raise NotImplementedError("Delete Item Method not implemented")

    async def list_items(self, query_params: dict):
        """
        Lists items from the database

        Args:
            query_params (dict): _description_
        """
        raise NotImplementedError("List Items Method not implemented")


class Tool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    description: str
    func: Optional[Callable[..., str]] = None
    block: Type[AIBlock]
