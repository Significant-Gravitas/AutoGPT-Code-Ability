import logging
from typing import List

from prisma.enums import DevelopmentPhase, FunctionState
from prisma.errors import PrismaError
from prisma.models import Function
from prisma.types import (
    FunctionCreateInput,
    FunctionUpdateInput,
    PackageCreateWithoutRelationsInput,
)

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ListValidationError,
    ValidatedResponse,
    ValidationError,
)
from codex.common.constants import TODO_COMMENT
from codex.common.database import INCLUDE_FUNC
from codex.common.logging import log_event
from codex.common.model import create_object_type
from codex.develop.code_validation import CodeValidator
from codex.develop.function import construct_function
from codex.develop.model import GeneratedFunctionResponse, Package

logger = logging.getLogger(__name__)


def parse_requirements(requirements_str: str) -> List[Package]:
    """
    Parses a string of requirements and creates a list of Package objects.

    Args:
    requirements_str (str): A string containing package requirements.

    Returns:
    List[Package]: A list of Package objects.
    """
    logger.debug("🔍 Parsing requirements...")
    packages = []
    version_specifiers = ["==", ">=", "<=", ">", "<", "~=", "!="]
    if requirements_str == "":
        return packages
    for line in requirements_str.splitlines():
        if line:
            # Remove comments and whitespace
            line = line.split("#")[0].strip()
            if not line:
                continue

            package_name, version, specifier = line, None, None

            # Try to split by each version specifier
            for spec in version_specifiers:
                if spec in line:
                    parts = line.split(spec)
                    package_name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else None
                    specifier = spec
                    break

            package = Package(
                package_name=package_name, version=version, specifier=specifier
            )
            packages.append(package)

    return packages


class DevelopAIBlock(AIBlock):
    developement_phase: DevelopmentPhase = DevelopmentPhase.DEVELOPMENT
    prompt_template_name = "develop"
    model = "gpt-4o"
    language = "python"

    async def validate(
        self,
        invoke_params: dict,
        response: ValidatedResponse,
        validation_errors: ListValidationError | None = None,
    ) -> ValidatedResponse:
        func_name = invoke_params.get("function_name", "")
        validation_errors = validation_errors or ListValidationError(
            f"Error developing `{func_name}`"
        )
        try:
            text = response.response

            # Package parsing
            requirement_blocks = text.split("```requirements")
            requirement_blocks.pop(0)
            if len(requirement_blocks) < 1:
                packages = []
            elif len(requirement_blocks) > 1:
                packages = []
                validation_errors.append_message(
                    f"There are {len(requirement_blocks)} requirements blocks in the response. "
                    + "There should be exactly 1"
                )
            else:
                packages: List[Package] = parse_requirements(
                    requirement_blocks[0].split("```")[0]
                )

            # Code parsing
            code_blocks = text.split("```python")
            code_blocks.pop(0)
            if len(code_blocks) == 0:
                raise ValidationError("No code blocks found in the response")
            elif len(code_blocks) > 1:
                logger.warning(
                    f"There are {len(code_blocks)} code blocks in the response. "
                    + "Pick the last one"
                )
            code = code_blocks[-1].split("```")[0]
            route_errors_as_todo = not invoke_params.get("will_retry_on_failure", True)
            response.response = await CodeValidator(
                compiled_route_id=invoke_params["compiled_route_id"],
                database_schema=invoke_params["database_schema"],
                function_name=invoke_params["function_name"],
                available_objects=invoke_params["available_objects"],
                available_functions=invoke_params["available_functions"],
                use_prisma=(self.language == "python"),
                use_nicegui=(self.language == "nicegui"),
            ).validate_code(
                packages=packages,
                raw_code=code,
                route_errors_as_todo=route_errors_as_todo,
                raise_validation_error=True,
            )

        except ValidationError as e:
            validation_errors.append_error(e)

        except Exception as e:
            # This is not a validation error we want to the agent to fix
            # it is a code bug in the validation logic
            logger.exception(
                "Unexpected error during validation",
                extra={"function_id": invoke_params["function_id"]},
            )
            raise e

        validation_errors.raise_if_errors()
        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ) -> Function:
        """
        Update an item in the database with the given identifiers
        and validated response.

        Args:
            ids (Identifiers): The identifiers of the item to be updated.
            validated_response (ValidatedResponse): The validated response
                                                containing the updated data.

        Returns:
            func: The updated item
        """
        generated_response: GeneratedFunctionResponse = validated_response.response

        for obj in generated_response.objects:
            generated_response.available_objects = await create_object_type(
                obj, generated_response.available_objects
            )

        function_defs: list[FunctionCreateInput] = []
        if generated_response.functions:
            for function in generated_response.functions:
                # Skip if the function is already available
                available_functions = generated_response.available_functions
                if function.name in available_functions:
                    same_func = available_functions[function.name]
                    function.validate_matching_function(same_func)
                    continue

                model = await construct_function(
                    function, generated_response.available_objects
                )
                model["CompiledRoute"] = {
                    "connect": {"id": generated_response.compiled_route_id}
                }
                function_defs.append(model)

        update_obj = FunctionUpdateInput(
            state=FunctionState.WRITTEN,
            Packages={
                "create": [
                    PackageCreateWithoutRelationsInput(
                        packageName=p.package_name,
                        version=p.version if p.version else "",
                        specifier=p.specifier if p.specifier else "",
                    )
                    for p in generated_response.packages
                ]
            },
            rawCode=generated_response.rawCode,
            importStatements=generated_response.imports,
            functionCode=generated_response.functionCode,
            template=generated_response.template,
            ChildFunctions={"create": function_defs},  # type: ignore
        )

        if not generated_response.function_id:
            raise AssertionError("Function ID is required to update")

        compiled_code = generated_response.get_compiled_code()
        if TODO_COMMENT in compiled_code:
            await log_event(
                id=ids,
                step=DevelopmentPhase.DEVELOPMENT,
                event="CODE_ERRORS_AS_TODO_COMMENTS",
                key=generated_response.function_id,
                data=f"{generated_response.db_schema}\n#-----#\n{compiled_code}",
            )

        func: Function | None = await Function.prisma().update(
            where={"id": generated_response.function_id},
            data=update_obj,
            include={
                **INCLUDE_FUNC["include"],
                "ParentFunction": INCLUDE_FUNC,
                "ChildFunctions": INCLUDE_FUNC,  # type: ignore
            },
        )
        if not func:
            raise AssertionError(
                f"Function with id {generated_response.function_id} not found"
            )

        logger.info(
            f"✅ Updated Function: {func.functionName} - {func.id}",
            extra=ids.model_dump(),
        )

        return func

    async def on_failed(self, ids: Identifiers, invoke_params: dict):
        function_name = invoke_params.get("function_name", "Unknown")
        function_signature = invoke_params.get("function_signature", "Unknown")
        try:
            logger.error(
                f"AI Failed to write the function {function_name}. Signature of failed function:\n{function_signature}",
                extra=ids.model_dump(),
            )
            await Function.prisma().update(
                where={"id": ids.function_id},
                data={"state": FunctionState.FAILED},
            )
        except PrismaError as pe:
            logger.exception(
                "Prisma error updating function state to FAILED.",
                pe,
                extra=ids.model_dump(),
            )
            raise pe
        except Exception as e:
            logger.exception(
                "Unexpected error updating function state to FAILED.",
                e,
                extra=ids.model_dump(),
            )
            raise e


class NiceGUIDevelopAIBlock(DevelopAIBlock):
    language = "nicegui"

    async def validate(
        self,
        invoke_params: dict,
        response: ValidatedResponse,
        validation_errors: ListValidationError | None = None,
    ) -> ValidatedResponse:
        function_name = invoke_params.get("function_name")
        route_path = invoke_params.get("route_path")

        response_text: str = response.response
        list_validation_error = validation_errors or ListValidationError(
            f"Error developing `{function_name}`"
        )

        if f"@ui.page('{route_path}')" not in response_text:
            list_validation_error.append_message(
                f"Missing @ui.page('{route_path}') decorator in the requested function {function_name}"
            )

        return await super().validate(invoke_params, response, list_validation_error)
