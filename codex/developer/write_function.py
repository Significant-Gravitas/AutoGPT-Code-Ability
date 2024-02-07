import ast
import logging
from typing import List

import black
import isort

from codex.architect.model import GeneratedCode
from codex.common.ai_block import (
    AIBlock,
    Indentifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.developer.model import Package

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
    def extract_type_hints(func_def):
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

    def validate_code(self, invoke_params: dict, code: str) -> bool:
        try:
            requested_node = invoke_params["requested_node"]

            sorted_content = isort.code(code)
            formatted_code = black.format_str(sorted_content, mode=black.FileMode())
            # We parse the code here to make sure it is valid
            parsed_code = ast.parse(formatted_code)
            args, ret = [], None

            for ast_node in ast.walk(parsed_code):
                if isinstance(ast_node, ast.FunctionDef):
                    args, ret = self.extract_type_hints(ast_node)
                    break

            errors = []
            if args != requested_node.args:
                errors.append(
                    f"Input parameter {args} does not match required parameter {requested_node.args}"
                )

            if ret != requested_node.return_type:
                errors.append(
                    f"Return type {ret} does not match required return type {requested_node.return_type}"
                )

            if errors:
                raise CodeValidationException(
                    f"Function Template: ```\n{formatted_code}\n```\n\nIssues with the code:\n\n"
                    + "\n".join(errors)
                )
            return formatted_code
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
        pass
