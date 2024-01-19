import ast
import logging
from typing import Dict, List

import black
import isort
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from codex.chains.gen_branching_graph import NodeDef, Param
from codex.model import RequiredPackage

logger = logging.getLogger(__name__)

code_model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
)


def parse_requirements(requirements_str: str) -> List[RequiredPackage]:
    """
    Parses a string of requirements and creates a list of RequiredPackage objects.

    Args:
    requirements_str (str): A string containing package requirements.

    Returns:
    List[RequiredPackage]: A list of RequiredPackage objects.
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

            package = RequiredPackage(
                package_name=package_name, version=version, specifier=specifier
            )
            packages.append(package)

    return packages


class CodeOutputParser(StrOutputParser):
    """OutputParser that parses LLMResult into the top likely string."""

    requested_node: NodeDef

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
        arg_types = {}
        for arg in func_def.args.args:
            # Extract argument name and type
            arg_name = arg.arg
            arg_type = arg.annotation
            if arg_type is not None:
                arg_types[arg_name] = ast.unparse(arg_type)

        # Extract return type
        return_type = None
        if func_def.returns:
            return_type = ast.unparse(func_def.returns)

        arg_types = [
            Param(param_type=arg_type.lower(), name=name, description="...")
            for name, arg_type in arg_types.items()
        ]
        return_type = Param(
            param_type=return_type.lower(), name="return", description="..."
        )
        return arg_types, return_type

    def validate_code(cls, code: str) -> bool:
        try:
            sorted_content = isort.code(code)
            formatted_code = black.format_str(sorted_content, mode=black.FileMode())
            # We parse the code here to make sure it is valid
            parsed_code = ast.parse(formatted_code)
            args, ret = [], None

            for ast_node in ast.walk(parsed_code):
                if isinstance(ast_node, ast.FunctionDef):
                    args, ret = cls.extract_type_hints(ast_node)
                    break

            errors = []
            for i, arg in enumerate(args):
                if arg != cls.requested_node.input_params[i]:
                    errors.append(
                        f"Input parameter {arg} does not match required parameter {cls.requested_node.input_params[i]}"
                    )

            if ret.param_type != cls.requested_node.get_return_type():
                errors.append(
                    f"Return type {ret.param_type} does not match required return type {cls.requested_node.get_return_type()}"
                )

            if errors:
                raise ValueError(f"Errors found in generated node code: {errors}")
            return formatted_code
        except Exception as e:
            raise ValueError(f"Error formatting code: {e}")

    def parse(self, text: str) -> str:
        """Returns the input text with no changes."""
        requirements, code = CodeOutputParser._sanitize_output(text)
        return parse_requirements(requirements), self.validate_code(code)


template = """You are an expect python developer. Write the python code to implement the node. Do not skip any implementation details.
Included error handling, comments and type hints.

Return only the requreirments and python imports and function in Markdown format, e.g.:

The requirements.txt
```requirements

```

The code.py
```python
....

Include only the function in the code.py file.
Do not include Example usage, Example response, or any other text.
Do not include InputParameterDef or OutputParameterDef
Validation failures should raise a ValueError with a helpful message.
```"""


def write_code_chain(
    invoke_params: Dict = {}, max_retries: int = 5, attempts: int = 0
) -> str:
    """Returns the input text with no changes."""
    parser_write_node = CodeOutputParser(requested_node=invoke_params["node"])

    prompt_write_node = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            (
                "human",
                "Write the function for the following node template: ```\n{node}\n```",
            ),
        ]
    )
    chain_write_node = prompt_write_node | code_model | parser_write_node
    while attempts < max_retries:
        try:
            return chain_write_node.invoke(
                invoke_params,
            )
        except Exception as e:
            attempts += 1
            logger.error(f"Error writing node: {e}")
            continue
    raise ValueError(f"Error writing node after {max_retries} attempts.")
