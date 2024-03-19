import logging
from typing import Iterable, List

from prisma.enums import DevelopmentPhase, FunctionState
from prisma.models import Function
from prisma.types import (
    FunctionCreateInput,
    FunctionUpdateInput,
    PackageCreateWithoutRelationsInput,
)

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.database import INCLUDE_FUNC
from codex.common.model import create_object_type
from codex.develop.code_validation import CodeValidator
from codex.develop.function import (
    construct_function,
)
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
    model = "gpt-4-0125-preview"
    langauge = "python"

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        validation_errors = []
        try:
            text = response.response

            # Package parsing
            requirement_blocks = text.split("```requirements")
            requirement_blocks.pop(0)
            if len(requirement_blocks) < 1:
                packages = []
            elif len(requirement_blocks) > 1:
                packages = []
                validation_errors.append(
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
            elif len(code_blocks) != 1:
                validation_errors.append(
                    f"There are {len(code_blocks)} code blocks in the response. "
                    + "There should be exactly 1"
                )
            code = code_blocks[0].split("```")[0]
            function_response = CodeValidator(invoke_params).validate_code(code)
            function_response.packages = packages
            function_response.compiled_route_id = invoke_params["compiled_route_id"]
            response.response = function_response

        except ValidationError as e:
            if isinstance(e.args[0], Iterable):
                validation_errors.extend(e.args[0])
            else:
                validation_errors.append(str(e))

        except Exception as e:
            # This is not a validation error we want to the agent to fix
            # it is a code bug in the validation logic
            logger.exception(e)
            raise e

        if validation_errors:
            # Important: ValidationErrors are used in the retry prompt
            errors = [f"\n  - {e}" for e in validation_errors]
            raise ValidationError(f"Error validating response:{''.join(errors)}")

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

        for obj in generated_response.objects.values():
            generated_response.available_objects = await create_object_type(
                obj, generated_response.available_objects
            )

        function_defs: list[FunctionCreateInput] = []
        if generated_response.functions:
            for function in generated_response.functions.values():
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
            ChildFunctions={"create": function_defs},  # type: ignore
        )

        if not generated_response.function_id:
            raise AssertionError("Function ID is required to update")

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

        logger.info(f"✅ Updated Function: {func.functionName} - {func.id}")

        return func
