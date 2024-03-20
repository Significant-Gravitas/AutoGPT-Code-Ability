import ast
import collections
import datetime
import json
import logging
import re
import subprocess
import tempfile
import typing

import prisma
from prisma.models import Function, ObjectType

from codex.common.ai_block import ValidationError
from codex.common.constants import PRISMA_FILE_HEADER
from codex.common.exec_external_tool import exec_external_on_contents
from codex.develop.compile import ComplicationFailure
from codex.develop.function_visitor import FunctionVisitor
from codex.develop.model import GeneratedFunctionResponse

logger = logging.getLogger(__name__)


class CodeValidator:
    def __init__(self, invoke_params: dict):
        self.db_schema: str = invoke_params["database_schema"]
        self.func_name: str = invoke_params["function_name"]
        self.available_functions: dict[str, Function] = invoke_params[
            "available_functions"
        ]
        self.available_objects: dict[str, ObjectType] = invoke_params[
            "available_objects"
        ]

    def validate_code(self, code: str) -> GeneratedFunctionResponse:
        """
        Validate the code snippet for any error
        Args:
            code (str): The code snippet to validate
        Returns:
            GeneratedFunctionResponse: The response of the validation
        Raise:
            ValidationError(e): The list of validation errors in the code snippet
        """
        validation_errors = []

        try:
            tree = ast.parse(code)
            visitor = FunctionVisitor()
            visitor.visit(tree)
            validation_errors.extend(visitor.errors)
        except Exception as e:
            raise ValidationError(f"Error parsing code: {e}")

        functions = visitor.functions.copy()

        # Validate that the main function is implemented.
        requested_func = functions.get(self.func_name)
        if not requested_func or not requested_func.is_implemented:
            raise ValidationError(
                f"Main Function body {self.func_name} is not implemented."
                f" Please complete the implementation of this function!"
            )
        requested_func.function_code = (
            "\n".join(visitor.globals) + "\n\n" + requested_func.function_code
        )

        # Validate that the main function is matching the expected signature.
        expected_func: Function | None = self.available_functions.get(self.func_name)
        if not expected_func:
            raise ComplicationFailure(f"Function {self.func_name} does not exist on DB")
        try:
            requested_func.validate_matching_function(expected_func)
        except Exception as e:
            validation_errors.append(str(e))

        # Validate that code is not re-declaring any existing entities.
        already_declared_entities = set(
            [
                obj.name
                for obj in visitor.objects.values()
                if obj.name in self.available_objects.keys()
            ]
            + [
                func.name
                for func in functions.values()
                if func.name in self.available_functions.keys()
            ]
        )
        if not already_declared_entities:
            validation_errors.append(
                "These class/function names has already been declared in the code, "
                "no need to declare them again: " + ", ".join(already_declared_entities)
            )
        del functions[self.func_name]

        result = GeneratedFunctionResponse(
            function_id=expected_func.id,
            function_name=expected_func.functionName,
            available_objects=self.available_objects,
            available_functions=self.available_functions,
            rawCode=code,
            imports=visitor.imports.copy(),
            objects=visitor.objects,
            template=requested_func.function_template or "",
            functionCode=requested_func.function_code,
            functions=functions,
            db_schema=self.db_schema,
            # These two values should be filled by the agent
            compiled_route_id="",
            packages=[],
        )

        # Execute static validators and fixers.
        old_compiled_code = result.regenerate_compiled_code()
        validation_errors.extend(validate_normalize_prisma(result))
        validation_errors.extend(static_code_analysis(result))
        new_compiled_code = result.get_compiled_code()

        # Auto-fixer works, retry validation
        if old_compiled_code != new_compiled_code:
            return self.validate_code(new_compiled_code)

        if validation_errors:
            raise ValidationError(validation_errors)

        return result


# ======= Static Code Validation Helper Functions =======#


def static_code_analysis(func: GeneratedFunctionResponse) -> list[str]:
    """
    Run static code analysis on the function code and mutate the function code to
    fix any issues.
    Args:
        func (GeneratedFunctionResponse):
            The function to run static code analysis on. `func` will be mutated.
    Returns:
        list[str]: The list of validation errors
    """
    validation_errors = []
    validation_errors += __execute_ruff(func)
    # validation_errors += __execute_pyright(func, func.rawCode)

    return validation_errors


def __execute_ruff(func: GeneratedFunctionResponse) -> list[str]:
    separator = "#------Code-Start------#"
    code = "\n".join(func.imports + [separator, func.rawCode])

    try:
        # Currently Disabled Rule List
        # E402 module level import not at top of file
        # F841 local variable is assigned to but never used
        code = exec_external_on_contents(
            command_arguments=[
                "ruff",
                "check",
                "--fix",
                "--ignore",
                "F841",
                "--ignore",
                "E402",
            ],
            file_contents=code,
            suffix=".py",
            raise_file_contents_on_error=True,
        )

        split = code.split(separator)
        func.imports = split[0].splitlines()
        func.rawCode = split[1].strip()
        return []

    except ValidationError as e:
        if len(e.args) > 1:
            # Ruff failed, but the code is reformatted
            code = e.args[1]
            e = e.args[0]

        validation_errors = [
            v
            for v in str(e).split("\n")
            if v.strip()
            if re.match(r"Found \d+ errors?\.", v) is None
        ]

        __fix_missing_imports(validation_errors, func)

        # Append problematic line to the error message
        split_pattern = r"(.+):(\d+):(\d+): (.+)"
        for i in range(len(validation_errors)):
            error_split = re.match(split_pattern, validation_errors[i])
            if not error_split:
                continue
            _, line, _, error = error_split.groups()
            problematic_line = code.splitlines()[int(line) - 1]
            validation_errors[i] = f"{error} -> '{problematic_line}'"

        return validation_errors


def __execute_pyright(func: GeneratedFunctionResponse, code: str) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        with open(f"{temp_dir}/schema.prisma", "w") as p:
            with open(f"{temp_dir}/code.py", "w") as f:
                # write the code to code.py
                f.write(code)
                f.flush()

                def execute_command(command: list[str]) -> str:
                    try:
                        result = subprocess.run(
                            command, check=True, cwd=temp_dir, capture_output=True
                        )
                        return result.stdout.decode("utf-8")
                    except subprocess.CalledProcessError as e:
                        return e.stdout.decode("utf-8")

                # TODO: start new python environment

                # run pipreqs save it to the requirements.txt
                result = execute_command(["pipreqs", "--force"])
                logger.debug(f"pipreqs response: {result}")

                # run pip install -r requirements.txt
                result = execute_command(["pip", "install", "-r", "requirements.txt"])
                logger.debug(f"pip response: {result}")

                # run prisma generate
                if func.db_schema:
                    p.write(PRISMA_FILE_HEADER + "\n" + func.db_schema)
                    p.flush()
                    result = execute_command(["prisma", "generate"])
                    logger.debug(f"prisma generate response: {result}")

                # execute pyright
                result = execute_command(
                    ["pyright", "--outputjson", "--exclude", "reportRedeclaration"]
                )
                logger.debug(f"pyright response: {result}")

                if not result:
                    return code

                errors = json.loads(result)
                raise errors


AUTO_IMPORT_TYPES: dict[str, str] = {
    "prisma": "import prisma",
    "BaseModel": "from pydantic import BaseModel",
    "Enum": "from enum import Enum",
}
for t in typing.__all__:
    AUTO_IMPORT_TYPES[t] = f"from typing import {t}"
for t in prisma.errors.__all__:
    AUTO_IMPORT_TYPES[t] = f"from prisma.errors import {t}"
for t in datetime.__all__:
    AUTO_IMPORT_TYPES[t] = f"from datetime import {t}"
for t in collections.__all__:
    AUTO_IMPORT_TYPES[t] = f"from collections import {t}"


def __fix_missing_imports(errors: list[str], func: GeneratedFunctionResponse):
    # parse "model X {" and "enum X {" from func.db_schema
    schema_imports = {}
    for entity in ["model", "enum"]:
        pattern = f"{entity}\\s+([a-zA-Z0-9_]+)\\s+{{"
        matches = re.findall(pattern, func.db_schema)
        for match in matches:
            schema_imports[match] = f"from prisma.{entity}s import {match}"

    missing_imports = []
    for error in errors:
        pattern = r"Undefined name `(.+?)`"
        match = re.search(pattern, error)
        if not match:
            continue

        missing_type = match.group(1)
        if missing_type in schema_imports:
            missing_imports.append(schema_imports[missing_type])
        elif missing_type in AUTO_IMPORT_TYPES:
            missing_imports.append(AUTO_IMPORT_TYPES[missing_type])

    func.imports = sorted(set(func.imports + list(missing_imports)))


def validate_normalize_prisma(func: GeneratedFunctionResponse) -> list[str]:
    """
    Validate and normalize the prisma code in the function
    Args:
        func (GeneratedFunctionResponse):
            The function to validate and normalize.
            compiled code, e.g: `func.rawCode` and `func.imports` will be mutated.
    Returns:
        list[str]: The list validation errors
    """
    validation_errors = []
    imports = func.imports
    code = func.rawCode

    if (".connect()" in code) or ("async with Prisma() as db:" in code):
        validation_errors.append(
            """
There is no need to use "await prisma_client.connect()" in the code it is already connected.

Database access should be done using the prisma.models, not using a prisma client.

import prisma.models

user = await prisma.models.User.prisma().create(
    data={
        'name': 'Robert',
        'email': 'robert@craigie.dev',
        'posts': {
            'create': {
                'title': 'My first post from Prisma!',
            },
        },
    },
)

"""
        )

    if "from prisma import Prisma" in code:
        validation_errors.append(
            "There is no need to do `from prisma import Prisma` as we are using the prisma.models to access the database."
        )

    def rename_code_variable(code: str, old_name: str, new_name: str) -> str:
        pattern = r"(?<!\.)\b{}\b".format(re.escape(old_name))
        return re.sub(pattern, new_name, code)

    def parse_import_alias(stmt: str) -> tuple[str, str]:
        if "import " not in stmt:
            return "", ""

        expr = stmt.split("import ")[1]
        if " as " in expr:
            name, alias = expr.split(" as ")
        else:
            name = alias = expr

        return name, alias

    for entity in ["model", "enum"]:
        new_imports = []
        for import_statement in imports:
            if f"from prisma.{entity}s import " in import_statement:
                name, alias = parse_import_alias(import_statement)
                code = rename_code_variable(code, alias, f"prisma.{entity}s.{name}")
                continue
            if f"from prisma import {entity}s" in import_statement:
                name, alias = parse_import_alias(import_statement)
                code = rename_code_variable(code, alias, f"prisma.{name}")
                continue
            new_imports.append(import_statement)

        imports = new_imports
        names = []
        model_pattern = f"prisma.{entity}s.([a-zA-Z0-9_]+)"
        for match in re.findall(model_pattern, code):
            names.append(match)

        for name in names:
            if f"{entity} {name} " in func.db_schema:
                continue

            # Sometimes, an enum is imported as a model and vice versa

            if entity == "model" and f"enum {name} " in func.db_schema:
                code = rename_code_variable(
                    code, f"prisma.models.{name}", f"prisma.enums.{name}"
                )
                continue

            if entity == "enum" and f"model {name} " in func.db_schema:
                code = rename_code_variable(
                    code, f"prisma.enums.{name}", f"prisma.models.{name}"
                )
                continue

            validation_errors.append(
                f"prisma.{entity}s.{name} is not available in the prisma schema. Only use models/enums available in the database schema."
            )

    # Make sure `import prisma` is added when `prisma.` usage is found in the code
    if "prisma." in code:
        imports.append("import prisma")

    # Sometimes it does this, it's not a valid import
    if "from pydantic import Optional" in imports:
        imports.remove("from pydantic import Optional")

    imports = sorted({i.strip() for i in imports})

    func.imports, func.rawCode = imports, code

    return validation_errors
