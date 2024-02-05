import ast
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

    def __init__(self, response: Any, usage_statistics: CompletionUsage):
        self.response = response
        self.usage_statistics = usage_statistics


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
            response=message.content, usage_statistics=usage_statistics
        )

    def validate(self, invoke_params: dict, response: ValidatedResponse) -> Any:
        text = response.response
        code = text.split("```python")[1].split("```")[0]

        tree = ast.parse(code)
        visitor = CodeGraphVisitor()
        visitor.visit(tree)

        functions = visitor.functions.copy()
        del functions[self.invoke_params["function_name"]]

        response.response = CodeGraph(
            function_name=self.function_name,
            api_route=self.invoke_params["api_route"],
            code_graph=visitor.functions[
                self.invoke_params["function_name"]
            ].function_template,
            imports=visitor.imports,
            function_defs=functions,
        )
        return response


class AIBlock:
    def __init__(
        self,
        name: str,
        system_prompt_template: str,
        user_prompt_template: str,
        retry_prompt_template: str,
        model: str,
        validator: Validator,
        is_json_response: bool,
        storeage_object: Any,
        oai_client: OpenAI,
        db_client: Prisma,
        template_base_path: str = "prompts",
    ):
        self.name = name
        self.system_prompt_template = system_prompt_template
        self.user_prompt_template = user_prompt_template
        self.retry_prompt_template = retry_prompt_template
        self.model = model
        self.validator = validator
        self.db_client = db_client
        self.storeage_object = storeage_object
        self.is_json_response = is_json_response
        self.oai_client = oai_client
        self.template_base_path = template_base_path

    def load_temaplate(self, template: str, invoke_params: dict) -> str:
        try:
            templates_dir = os.path.join(
                os.path.dirname(__file__), f"../{self.template_base_path}/{self.model}"
            )
            templates_dir = pathlib.Path(templates_dir).resolve(strict=True)
            templates_env = Environment(loader=FileSystemLoader(templates_dir))
            prompt_template = templates_env.get_template(f"{template}.j2")
            return prompt_template.render(**invoke_params)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            raise PromptTemplateInvocationError(f"Error loading template: {e}")

    def invoke(self, invoke_params: dict, max_retries=3) -> Any:
        retries = 0
        try:
            system_prompt = self.load_temaplate(
                self.system_prompt_template, invoke_params
            )
            user_prompt = self.load_temaplate(self.user_prompt_template, invoke_params)

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
            validated_response = self.validator.run(invoke_params, response)
        except ValidationError as e:
            while retries < max_retries:
                retries += 1
                try:
                    invoke_params["error_msg"] = str(e)
                    retry_prompt = self.load_temaplate(
                        self.retry_prompt_template, invoke_params
                    )
                    request_params["messages"] = (
                        [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": retry_prompt},
                        ],
                    )
                    response = self.oai_client.chat.completions.create(**request_params)
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

        return validated_response.response

    async def save_output(self, validated_response: ValidatedResponse):
        raise NotImplementedError("save_output method not implemented")

    async def update_item(self, item: Any):
        raise NotImplementedError("update_item method not implemented")

    async def get_item(self, item_id: str):
        raise NotImplementedError("get_item method not implemented")

    async def delete_item(self, item_id: str):
        raise NotImplementedError("delete_item method not implemented")

    async def list_items(self, item_id: str, page: int, page_size: int):
        raise NotImplementedError("list_items method not implemented")

    def routes(self):
        base_router = APIRouter()

        @base_router.get(f"/{self.name}s")
        async def list_objects(
            request: Request,
            page: Optional[int] = Query(1, ge=1),
            page_size: Optional[int] = Query(10, ge=1),
        ):
            pass

        @base_router.get(f"/{self.name}/{id}")
        async def get_object(
            request: Request,
            id: int,
        ):
            pass

        @base_router.post(f"/{self.name}")
        async def create_object(
            request: Request,
        ):
            pass

        @base_router.patch(f"/{self.name}/{id}")
        async def update_object(
            request: Request,
            id: int,
        ):
            pass

        @base_router.delete(f"/{self.name}/{id}")
        async def delete_object(
            request: Request,
            id: int,
        ):
            pass


if __name__ == "__main__":
    import codex.common.logging_config

    codex.common.logging_config.setup_logging()

    ois_client = OpenAI()

    block = AIBlock(
        name="code-graph",
        system_prompt_template="cg.sys.python",
        user_prompt_template="cg.usr.python",
        retry_prompt_template="cg.rty.python",
        model="gpt-4-0125-preview",
        validator=Validator(),
        is_json_response=False,
        storeage_object=None,
        oai_client=ois_client,
        db_client=None,
    )
    ans = block.invoke(
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

    import IPython

    IPython.embed()

    IPython.embed()
