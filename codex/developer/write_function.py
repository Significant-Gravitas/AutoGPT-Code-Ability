import ast
import logging
from typing import List

import black
import isort
from prisma.models import Functions as FunctionsDBModel
from prisma.types import FunctionsCreateInput, PackageCreateWithoutRelationsInput

from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.developer.model import Function, GeneratedCode, Package

logger = logging.getLogger(__name__)


class CodeValidationException(Exception):
    pass


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


class WriteFunctionAIBlock(AIBlock):
    prompt_template_name = "write_function"
    model = "gpt-4-0125-preview"
    langauge = "python"

    @staticmethod
    def _sanitize_output(text: str):
        # Initialize variables to store requirements and code
        requirements = text.split("```requirements")
        if len(requirements) > 1:
            requirements = text.split("```requirements")[1].split("```")[0]
        else:
            requirements = ""
        code = text.split("```python")[1].split("```")[0]
        logger.debug(f"Requirements: {requirements}")
        logger.debug(f"Code: {code}")
        return requirements, code

    @staticmethod
    def extract_type_hints(func_def) -> tuple[str, str]:
        args = []
        for arg in func_def.args.args:
            arg_type = ast.unparse(arg.annotation) if arg.annotation else "Unknown"
            args.append(arg_type)
        args_str = ", ".join(args)

        # Extract return type
        return_type = "Unkown"
        if func_def.returns:
            return_type = ast.unparse(func_def.returns)

        return args_str, return_type

    def validate_code(self, invoke_params: dict, code: str) -> Function:
        try:
            function_def = invoke_params["function_def"]

            sorted_content = isort.code(code)
            formatted_code = black.format_str(sorted_content, mode=black.FileMode())
            # We parse the code here to make sure it is valid
            parsed_code = ast.parse(formatted_code)
            args, ret = "", ""
            docstring = ""
            generated_func_name = ""

            for ast_node in ast.walk(parsed_code):
                if isinstance(ast_node, ast.FunctionDef):
                    args, ret = self.extract_type_hints(ast_node)
                    docstring = ast.get_docstring(ast_node)
                    generated_func_name = ast_node.name
                    break

            errors = []
            if generated_func_name != function_def.name:
                errors.append(
                    f"Function name {generated_func_name} does not match"
                    f"required function name {function_def.name}"
                )
            if args.lower() != function_def.args.lower():
                errors.append(
                    f"Input parameter {args} does not match required "
                    f"parameter {function_def.args}"
                )

            if ret.lower() != function_def.return_type.lower():
                errors.append(
                    f"Return type {ret} does not match required return type "
                    f"{function_def.return_type}"
                )

            if errors:
                raise CodeValidationException(
                    f"Function Template: ```\n{formatted_code}\n```\n\n"
                    "Issues with the code:\n\n" + "\n".join(errors)
                )

            return Function(
                name=function_def.name,
                doc_string=docstring if docstring else function_def.doc_string,
                args=args,
                return_type=ret,
                code=formatted_code,
            )
        except Exception as e:
            raise ValueError(f"Error formatting code: {e}")

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        try:
            requirements, code = self._sanitize_output(response.message)
            packages = parse_requirements(requirements)
            code = self.validate_code(invoke_params, code)

            response.response = GeneratedCode(packages=packages, code=code)
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Indentifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        genfunc = validated_response.response.code

        create_data = FunctionsCreateInput(
            name=genfunc.name,
            doc_string=genfunc.doc_string,
            args=genfunc.args,
            return_type=genfunc.return_type,
            code=genfunc.code,
            functionDefs={"connect": {"id": ids.function_def_id}},
        )

        if validated_response.response.packages:
            package_create_data = [
                PackageCreateWithoutRelationsInput(
                    packageName=package.package_name,
                    # TODO: Fix db schema to allow null values
                    # This is a work around to avoid merg nightmares with the db schema
                    version=package.version if package.version else " ",
                    specifier=package.specifier if package.specifier else " ",
                )
                for package in validated_response.response.packages
            ]
            create_data = FunctionsCreateInput(
                name=genfunc.name,
                doc_string=genfunc.doc_string,
                args=genfunc.args,
                return_type=genfunc.return_type,
                code=genfunc.code,
                packages={"create": package_create_data},
                functionDefs={"connect": {"id": ids.function_def_id}},
            )
        else:
            create_data = FunctionsCreateInput(
                name=genfunc.name,
                doc_string=genfunc.doc_string,
                args=genfunc.args,
                return_type=genfunc.return_type,
                code=genfunc.code,
                functionDefs={"connect": {"id": ids.function_def_id}},
            )

        func = await FunctionsDBModel.prisma().create(data=create_data)
        return func
