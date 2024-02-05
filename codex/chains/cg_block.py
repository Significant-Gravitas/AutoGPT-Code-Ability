import ast
import hashlib
import json
import logging
import os
import pathlib
from typing import Any, Optional

from fastapi import APIRouter, Query, Request, Response, UploadFile
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion
from prisma import Prisma

from codex.chains.code_graph import CodeGraph, CodeGraphVisitor

logger = logging.getLogger(__name__)


class LLMFailure(Exception):
    pass


class ParsingError(Exception):
    pass


class ValidationError(Exception):
    pass


class PromptTemplateInvocationError(Exception):
    pass


class ValidatedResponse:
    response: Any
    usage_statistics: CompletionUsage
    message: str

    def __init__(self, response: Any, usage_statistics: CompletionUsage, message: str):
        self.response = response
        self.usage_statistics = usage_statistics
        self.message = message


class Validator:
    def run(self, invoke_params: dict, response: ChatCompletion) -> Any:
        parsed_response = self.parse(response)
        validated_resposne = self.validate(invoke_params, parsed_response)
        return validated_resposne

    def parse(self, response: ChatCompletion) -> Any:
        usage_statistics = response.usage
        message = response.choices[0].message

        if message.tool_calls != None:
            raise NotImplementedError("Tool calls are not supported")
        elif message.function_call != None:
            raise NotImplementedError("Function calls are not supported")

        return ValidatedResponse(
            response=message.content,
            usage_statistics=usage_statistics,
            message=message.content,
        )

    def validate(self, invoke_params: dict, response: ValidatedResponse) -> Any:
        text = response.response
        code = text.split("```python")[1].split("```")[0]

        tree = ast.parse(code)
        visitor = CodeGraphVisitor()
        visitor.visit(tree)

        functions = visitor.functions.copy()
        del functions[invoke_params["function_name"]]

        response.response = CodeGraph(
            function_name=invoke_params["function_name"],
            api_route=invoke_params["api_route"],
            code_graph=visitor.functions[
                invoke_params["function_name"]
            ].function_template,
            imports=visitor.imports,
            function_defs=functions,
        )
        return response


class AIBlock:
    def __init__(
        self,
        name: str,
        prompt_template_name: str,
        model: str,
        validator: Validator,
        is_json_response: bool,
        storeage_object: Any,
        oai_client: OpenAI,
        db_client: Prisma,
        template_base_path: str = "prompts",
    ):
        self.name = name
        self.prompt_template_name = prompt_template_name
        self.model = model
        self.validator = validator
        self.db_client = db_client
        self.storeage_object = storeage_object
        self.is_json_response = is_json_response
        self.oai_client = oai_client
        self.template_base_path = os.path.join(
            os.path.dirname(__file__), f"../{template_base_path}/{self.model}"
        )
        self.templates_dir = pathlib.Path(self.template_base_path).resolve(strict=True)

        self.generate_template_hash()
        self.call_template_id = None

    def generate_template_hash(self):
        template_str = ""
        with open(
            f"{self.templates_dir}/{self.prompt_template_name}.system.j2", "r"
        ) as f:
            template_str += f.read()

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}.user.j2", "r"
        ) as f:
            template_str += f.read()

        with open(
            f"{self.templates_dir}/{self.prompt_template_name}.retry.j2", "r"
        ) as f:
            template_str += f.read()

        self.template_hash = hashlib.md5(template_str.encode()).hexdigest()

    async def store_call_template(self):
        from prisma.models import LLMCallTemplate

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
                }
            )

        # Disconnect from the database
        await self.db_client.disconnect()

        # Store the call template ID for future use
        self.call_template_id = call_template.id

        return call_template

    async def store_call_attempt(
        self, response: ValidatedResponse, attempt: int, prompt: str
    ):
        from prisma.models import LLMCallAttempt

        await self.db_client.connect()

        assert self.call_template_id, "Call template ID not set"

        call_attempt = await LLMCallAttempt.prisma().create(
            data={
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

    async def invoke(self, invoke_params: dict, max_retries=3) -> Any:
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

            presponse = self.validator.parse(response)

            await self.store_call_attempt(
                presponse,
                retries,
                request_params["messages"],
            )

            validated_response = self.validator.run(invoke_params, response)
        except ValidationError as e:
            while retries < max_retries:
                retries += 1
                try:
                    invoke_params["error_msg"] = str(e)
                    retry_prompt = self.load_temaplate("retry", invoke_params)
                    request_params["messages"] = (
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": retry_prompt},
                        ],
                    )
                    response = self.oai_client.chat.completions.create(**request_params)
                    presponse = self.validator.parse(response)

                    await self.store_call_attempt(
                        presponse,
                        retries,
                        request_params["messages"],
                    )
                    validated_response = self.validator.run(invoke_params, response)
                    break
                except Exception as e:
                    logger.error(
                        f"{retries}/{max_retries} Error validating response: {e}"
                    )
                    continue
        except Exception as e:
            logger.error(f"Error invoking AIBlock: {e}")
            raise LLMFailure(f"Error invoking AIBlock: {e}")

        await self.save_output(validated_response)

        return validated_response.response

    async def save_output(self, validated_response: ValidatedResponse):
        from prisma.models import CodeGraph

        await self.db_client.connect()

        cg = await CodeGraph.prisma().create(
            data={
                "function_name": validated_response.response.function_name,
                "api_route": validated_response.response.api_route,
                "code_graph": validated_response.response.code_graph,
                "imports": validated_response.response.imports,
            }
        )

        await self.db_client.disconnect()

        return cg

    async def update_item(self, item: Any):
        from prisma.models import CodeGraph

        await self.db_client.connect()

        cg = await CodeGraph.prisma().update(
            where={"id": item.id},
            data={
                "function_name": item.function_name,
                "api_route": item.api_route,
                "code_graph": item.code_graph,
                "imports": item.imports,
            },
        )

        await self.db_client.disconnect()

        return cg

    async def get_item(self, item_id: str):
        from prisma.models import CodeGraph

        await self.db_client.connect()

        cg = await CodeGraph.prisma().find_unique(where={"id": item_id})

        await self.db_client.disconnect()

        return cg

    async def delete_item(self, item_id: str):
        from prisma.models import CodeGraph

        await self.db_client.connect()

        cg = await CodeGraph.prisma().delete(where={"id": item_id})

        await self.db_client.disconnect()

    async def list_items(self, item_id: str, page: int, page_size: int):
        from prisma.models import CodeGraph

        await self.db_client.connect()

        cg = await CodeGraph.prisma().find_many(
            skip=(page - 1) * page_size, take=page_size
        )

        await self.db_client.disconnect()

        return cg

    def routes(self):
        base_router = APIRouter()

        @base_router.get("/codegraphs")
        async def list_objects(
            request: Request,
            page: Optional[int] = Query(1, ge=1),
            page_size: Optional[int] = Query(10, ge=1),
        ):
            return await self.list_items(page, page_size)

        @base_router.get("/codegraph/{id}")
        async def get_object(
            request: Request,
            id: int,
        ):
            return await self.get_item(id)

        @base_router.post("/codegraph")
        async def create_object(
            request: Request,
        ):
            return await self.save_output(request)

        @base_router.patch("/codegraph/{id}")
        async def update_object(
            request: Request,
            id: int,
        ):
            return await self.update_item(request)

        @base_router.delete("/codegraph/{id}")
        async def delete_object(
            request: Request,
            id: int,
        ):
            return await self.delete_item(id)


if __name__ == "__main__":
    import asyncio

    import codex.common.logging_config

    codex.common.logging_config.setup_logging()

    ois_client = OpenAI()

    block = AIBlock(
        name="code-graph",
        prompt_template_name="cg.python",
        model="gpt-4-0125-preview",
        validator=Validator(),
        is_json_response=False,
        storeage_object=None,
        oai_client=ois_client,
        db_client=Prisma(auto_register=True),
    )
    ans = asyncio.run(
        block.invoke(
            {
                "api_route": "/api/v1/availability",
                "function_name": "check_availability",
                "description": """### **Overview**

The function is designed to return the real-time availability status of professionals, dynamically updated based on their current activity or schedule. It operates without the need for database access, relying instead on real-time or pre-set schedule data provided at the time of the query.

### **Input**

1. **Current Time:** The timestamp at which the availability status is being requested.
2. **Schedule Data:** A pre-set schedule for the professional, including start and end times of appointments or busy periods.

### **Process**

1. **Validation:** Check if the **Schedule** **Data** is valid and if the current time is provided in the correct format.
2. **Determine Availability:**
    - If schedule data is provided, the function compares the current time against the schedule to determine if the professional is currently in an appointment or busy period.
    - If no schedule data is provided, the function assumes the professional's status is assumed to be 'Available' .

### **Output**

1. **Availability Status:** A response indicating the professional's current availability status. The status can be:
    - 'Available' - The professional is free and can accept appointments.
    - 'Busy' - The professional is currently occupied and cannot accept appointments.""",
            }
        )
    )

    import IPython

    IPython.embed()
