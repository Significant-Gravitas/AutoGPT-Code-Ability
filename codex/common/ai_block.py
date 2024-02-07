import hashlib
import json
import logging
import os
import pathlib
from typing import Any

from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion
from prisma import Prisma
from pydantic import BaseModel

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


class Indentifiers(BaseModel):
    user_id: int
    app_id: int
    spec_id: int | None = None
    completed_app_id: int | None = None
    deployment_id: int | None = None


class AIBlock:
    """
    The AI BLock is a base class for all AI Blocks. It provides a common interface for
    calling an LLM, parsing the response, validating the response, and then storing it
    along with the call attempt in the database.

    It also holds the database call logic for creating, updating, getting, and deleting
    objects generated from the AI Block.

    YOU MUST IMPLEMENT THE FOLLOWING METHODS:
        - def validate(self, invoke_params: dict, response: ValidatedResponse) -> ValidatedResponse:
        - async def create_item(self, validated_response: ValidatedResponse):

    You should also implement theses methods if you want to use the database logic:
        - async def update_item(self, query_params: dict):
        - async def get_item(self, query_params: dict):
        - async def delete_item(self, query_params: dict):
        - async def list_items(self, query_params: dict):
    """

    prompt_template_name = ""
    langauge = None
    model = ""
    is_json_response = False
    template_base_path = "prompts"

    def __init__(
        self,
        oai_client: OpenAI,
        db_client: Prisma,
    ):
        """
        Args:
            oai_client (OpenAI): The OpenAI client
            db_client (Prisma): The Prisma Database client
        """
        self.db_client = db_client
        self.oai_client = oai_client
        self.template_base_path = os.path.join(
            os.path.dirname(__file__), f"../{self.template_base_path}/{self.model}"
        )
        self.templates_dir = pathlib.Path(self.template_base_path).resolve(strict=True)
        self.call_template_id = None
        self.set_prompt_template_name()

    async def store_call_template(self):
        from prisma.models import LLMCallTemplate

        template_str = ""
        lang_str = ""
        if self.langauge:
            lang_str = f"{self.langauge}."
        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}system.j2", "r"
        ) as f:
            system_prompt = f.read()
            template_str += system_prompt

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}user.j2", "r"
        ) as f:
            user_prompt = f.read()
            template_str += user_prompt

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}/{lang_str}retry.j2", "r"
        ) as f:
            retry_prompt = f.read()
            template_str += retry_prompt

        self.template_hash = hashlib.md5(template_str.encode()).hexdigest()

        # Connect to the database
        await self.db_client.connect()

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
                }
            )

        # Disconnect from the database
        await self.db_client.disconnect()

        # Store the call template ID for future use
        self.call_template_id = call_template.id

        return call_template

    async def store_call_attempt(
        self,
        user_id: int,
        app_id: int,
        response: ValidatedResponse,
        attempt: int,
        prompt: str,
    ):
        from prisma.models import LLMCallAttempt

        await self.db_client.connect()

        assert self.call_template_id, "Call template ID not set"

        call_attempt = await LLMCallAttempt.prisma().create(
            data={
                "userId": user_id,
                "appId": app_id,
                "callTemplateId": self.call_template_id,
                "completionTokens": response.usage_statistics.completion_tokens,
                "promptTokens": response.usage_statistics.prompt_tokens,
                "totalTokens": response.usage_statistics.total_tokens,
                "attempt": attempt,
                "prompt": json.dumps(prompt) if not isinstance(prompt, str) else prompt,
                "response": response.message,
                "model": self.model,
            }
        )

        await self.db_client.disconnect()

        return call_attempt

    def load_temaplate(self, template: str, invoke_params: dict) -> str:
        try:
            templates_env = Environment(loader=FileSystemLoader(self.templates_dir))
            prompt_template = templates_env.get_template(
                f"{self.prompt_template_name}.{template}.j2"
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

    async def invoke(
        self, ids: Indentifiers, invoke_params: dict, max_retries=3
    ) -> Any:
        if not self.call_template_id:
            await self.store_call_template()

        retries = 0
        try:
            system_prompt = self.load_temaplate("system", invoke_params)
            user_prompt = self.load_temaplate("user", invoke_params)

            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 4095,
                "temperature": 1,
            }
            if self.is_json_response:
                request_params["response_format"] = {"type": "json_object"}

            response = self.oai_client.chat.completions.create(**request_params)

            presponse = self.parse(response)

            await self.store_call_attempt(
                ids.user_id,
                ids.app_id,
                presponse,
                retries,
                request_params["messages"],
            )

            validated_response = self.validate(invoke_params, presponse)
        except ValidationError as e:
            while retries < max_retries:
                retries += 1
                try:
                    invoke_params["generation"] = presponse.message
                    invoke_params["error"] = str(e)

                    retry_prompt = self.load_temaplate("retry", invoke_params)
                    request_params["messages"] = (
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": retry_prompt},
                        ],
                    )
                    response = self.oai_client.chat.completions.create(**request_params)
                    presponse = self.parse(response)

                    await self.store_call_attempt(
                        presponse,
                        retries,
                        request_params["messages"],
                    )
                    validated_response = self.validate(ids, presponse)
                    break
                except Exception as e:
                    logger.error(
                        f"{retries}/{max_retries} Error validating response: {e}"
                    )
                    continue
        except Exception as e:
            logger.error(f"Error invoking AIBlock: {e}")
            raise LLMFailure(f"Error invoking AIBlock: {e}")

        await self.create_item(ids, validated_response)

        return validated_response.response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
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
