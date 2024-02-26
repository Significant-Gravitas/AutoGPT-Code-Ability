import hashlib
import logging
import os
import pathlib
from typing import Any

from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion
from prisma.enums import DevelopmentPhase
from prisma.fields import Json
from prisma.models import LLMCallAttempt, LLMCallTemplate
from pydantic import BaseModel

from codex.api_model import Identifiers
from codex.common.ai_model import OpenAIChatClient

logger = logging.getLogger(__name__)


class LLMFailure(Exception):
    pass


class ParsingError(Exception):
    pass


class ValidationError(Exception):
    pass


class PromptTemplateInvocationError(Exception):
    pass


class ValidatedResponse(BaseModel):
    response: Any
    usage_statistics: CompletionUsage
    message: str

    class config:
        arbitrary_types_allowed = True


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
    langauge = None
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
        self.oai_client: AsyncOpenAI = OpenAIChatClient.get_instance().openai
        self.template_base_path = os.path.join(
            os.path.dirname(__file__),
            f"../{self.template_base_path}/{self.model}",
        )
        self.templates_dir = pathlib.Path(self.template_base_path).resolve(strict=True)
        self.call_template_id = None
        self.load_pydantic_format_instructions()

    def load_pydantic_format_instructions(self):
        if self.pydantic_object:
            schema = self.pydantic_object.schema_json()

            template_dir = os.path.join(
                os.path.dirname(__file__),
                f"../prompts/techniques/",
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
        template_str = ""
        lang_str = ""
        if self.langauge:
            lang_str = f"{self.langauge}."
        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}system.j2",
            "r",
        ) as f:
            system_prompt = f.read()
            template_str += system_prompt

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}user.j2",
            "r",
        ) as f:
            user_prompt = f.read()
            template_str += user_prompt

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}retry.j2",
            "r",
        ) as f:
            retry_prompt = f.read()
            template_str += retry_prompt

        self.template_hash = hashlib.md5(template_str.encode()).hexdigest()

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
                    "systemPrompt": system_prompt,
                    "userPrompt": user_prompt,
                    "retryPrompt": retry_prompt,
                    "developmentPhase": self.developement_phase,
                }
            )

        # Store the call template ID for future use
        self.call_template_id = call_template.id

        return call_template

    async def store_call_attempt(
        self,
        user_id: str,
        app_id: str,
        response: ValidatedResponse,
        attempt: int,
        prompt: Json,
    ):
        assert self.call_template_id, "Call template ID not set"

        call_attempt = await LLMCallAttempt.prisma().create(
            data={
                "User": {"connect": {"id": user_id}},
                "Application": {"connect": {"id": app_id}},
                "LLMCallTemplate": {"connect": {"id": self.call_template_id}},
                "completionTokens": response.usage_statistics.completion_tokens,
                "promptTokens": response.usage_statistics.prompt_tokens,
                "totalTokens": response.usage_statistics.total_tokens,
                "attempt": attempt,
                "prompt": prompt,
                "response": response.message,
                "model": self.model,
            }
        )
        return call_attempt

    def load_temaplate(self, template: str, invoke_params: dict) -> str:
        try:
            lang_str = ""
            if self.langauge:
                lang_str = f"{self.langauge}."
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

    def validate(
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

    async def invoke(self, ids: Identifiers, invoke_params: dict, max_retries=3) -> Any:
        validated_response = None
        if not self.call_template_id:
            await self.store_call_template()
        presponse = None
        retries = 0
        try:
            if self.is_json_response:
                invoke_params["format_instructions"] = self.get_format_instructions()
            system_prompt = self.load_temaplate("system", invoke_params)
            user_prompt = self.load_temaplate("user", invoke_params)

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
            response = await self.oai_client.chat.completions.create(**request_params)

            presponse = self.parse(response)

            await self.store_call_attempt(
                ids.user_id,
                ids.app_id,
                presponse,
                retries,
                Json(request_params["messages"]),
            )

            validated_response = self.validate(invoke_params, presponse)
        except ValidationError as validation_error:
            logger.warning(f"Failed initial generation attempt: {validation_error}")
            error_message = validation_error
            while retries < max_retries:
                retries += 1
                try:
                    if presponse:
                        invoke_params["generation"] = presponse.message
                    else:
                        invoke_params["generation"] = "Error generating response"
                    invoke_params["error"] = str(error_message)

                    retry_prompt = self.load_temaplate("retry", invoke_params)
                    request_params["messages"] = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": retry_prompt},
                    ]
                    response = await self.oai_client.chat.completions.create(
                        **request_params
                    )
                    presponse = self.parse(response)
                    assert request_params["messages"], "Messages not set"

                    await self.store_call_attempt(
                        ids.user_id,
                        ids.app_id,
                        presponse,
                        retries,
                        Json(request_params["messages"]),
                    )
                    validated_response = self.validate(invoke_params, presponse)
                    break
                except Exception as retry_error:
                    logger.warning(
                        f"{retries}/{max_retries}"
                        + f" Failed validating response: {retry_error}"
                    )
                    continue
            if not validated_response:
                raise LLMFailure(f"Error validating response: {validation_error}")
        except Exception as unkown_error:
            logger.error(f"Error invoking AIBlock: {unkown_error}")
            raise LLMFailure(f"Error invoking AIBlock: {unkown_error}")

        stored_obj = await self.create_item(ids, validated_response)
        return stored_obj if stored_obj else validated_response.response

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
