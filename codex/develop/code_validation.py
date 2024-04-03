import ast
import collections
import datetime
import json
import logging
import os
import re
import typing

import black
import isort
import prisma
from prisma.models import Function, ObjectType

from codex.common.ai_block import (
    LineValidationError,
    ListValidationError,
    ValidationError,
    ValidationErrorWithContent,
)
from codex.common.constants import PRISMA_FILE_HEADER
from codex.common.exec_external_tool import (
    DEFAULT_DEPS,
    PROJECT_TEMP_DIR,
    exec_external_on_contents,
    execute_command,
    setup_if_required,
)
from codex.common.model import FunctionDef
from codex.develop.function import generate_object_code
from codex.develop.function_visitor import FunctionVisitor
from codex.develop.model import GeneratedFunctionResponse, Package

logger = logging.getLogger(__name__)


class CodeValidator:
    def __init__(
        self,
        compiled_route_id: str,
        database_schema: str,
        function_name: str | None = None,
        available_functions: dict[str, Function] | None = None,
        available_objects: dict[str, ObjectType] | None = None,
    ):
        self.compiled_route_id: str = compiled_route_id
        self.db_schema: str = database_schema
        self.func_name: str = function_name or ""
        self.available_functions: dict[str, Function] = available_functions or {}
        self.available_objects: dict[str, ObjectType] = available_objects or {}

    async def reformat_code(
        self,
        code: str,
        packages: list[Package],
    ) -> str:
        """
        Reformat the code snippet
        Args:
            code (str): The code snippet to reformat
            packages (list[Package]): The list of packages to validate
        Returns:
            str: The reformatted code snippet
        """
        try:
            code = (
                await self.validate_code(
                    raw_code=code,
                    packages=packages,
                    route_errors_as_todo=True,
                    raise_validation_error=False,
                )
            ).get_compiled_code()
        except Exception as e:
            # We move on with unfixed code if there's an error
            logger.warning(
                f"Error formatting code for route #{self.compiled_route_id}: {e}"
            )

        for formatter in [
            lambda code: isort.code(code),
            lambda code: black.format_str(code, mode=black.FileMode()),
        ]:
            try:
                code = formatter(code)
            except Exception as e:
                # We move on with unformatted code if there's an error
                logger.warning(
                    f"Error formatting code for route #{self.compiled_route_id}: {e}"
                )

        return code

    async def validate_code(
        self,
        packages: list[Package],
        raw_code: str,
        route_errors_as_todo: bool = False,
        raise_validation_error: bool = True,
        call_cnt: int = 0,
    ) -> GeneratedFunctionResponse:
        """
        Validate the code snippet for any error
        Args:
            packages (list[Package]): The list of packages to validate
            raw_code (str): The code snippet to validate
        Returns:
            GeneratedFunctionResponse: The response of the validation
        Raise:
            ValidationError(e): The list of validation errors in the code snippet
        """
        validation_errors: list[ValidationError] = []

        try:
            tree = ast.parse(raw_code)
            visitor = FunctionVisitor()
            visitor.visit(tree)
            validation_errors.extend([ValidationError(e) for e in visitor.errors])
        except Exception as e:
            # parse invalid code line and add it to the error message
            error = f"Error parsing code: {e}"
            if line := re.search(r"line (\d+)", error):
                raise LineValidationError(
                    error=error, code=raw_code, line_from=int(line.group(1))
                )
            else:
                raise ValidationError(error)

        # Eliminate duplicate visitor.functions and visitor.objects, prefer the last one
        visitor.imports = list(set(visitor.imports))
        visitor.functions = list({f.name: f for f in visitor.functions}.values())
        visitor.objects = list(
            {
                o.name: o
                for o in visitor.objects
                if o.name not in self.available_objects
            }.values()
        )

        # Add implemented functions into the main function, only link the stub functions
        deps_funcs = [f for f in visitor.functions if f.is_implemented]
        stub_funcs = [f for f in visitor.functions if not f.is_implemented]

        objects_block = zip(
            ["\n\n" + generate_object_code(obj) for obj in visitor.objects],
            visitor.objectsIdx,
        )
        functions_block = zip(
            ["\n\n" + fun.function_code for fun in deps_funcs], visitor.functionsIdx
        )
        globals_block = zip(
            ["\n\n" + glob for glob in visitor.globals], visitor.globalsIdx
        )
        function_code = "".join(
            code
            for code, _ in sorted(
                list(objects_block) + list(functions_block) + list(globals_block),
                key=lambda x: x[1],
            )
        ).strip()

        # No need to validate main function if it's not provided (compiling a server code)
        if self.func_name:
            func_id, main_func = self.__validate_main_function(
                deps_funcs=deps_funcs,
                function_code=function_code,
                validation_errors=validation_errors,
            )
            function_template = main_func.function_template
        else:
            func_id = None
            function_template = None

        # Validate that code is not re-declaring any existing entities.
        already_declared_entities = set(
            [
                obj.name
                for obj in visitor.objects
                if obj.name in self.available_objects.keys()
            ]
            + [
                func.name
                for func in visitor.functions
                if func.name in self.available_functions.keys()
            ]
        )
        if not already_declared_entities:
            validation_errors.append(
                ValidationError(
                    "These class/function names has already been declared in the code, "
                    "no need to declare them again: "
                    + ", ".join(already_declared_entities)
                )
            )

        result = GeneratedFunctionResponse(
            function_id=func_id,
            function_name=self.func_name,
            available_objects=self.available_objects,
            available_functions=self.available_functions,
            rawCode=function_code,
            imports=visitor.imports.copy(),
            objects=[],  # Objects will be bundled in the function_code instead.
            template=function_template or "",
            functionCode=function_code,
            functions=stub_funcs,
            db_schema=self.db_schema,
            packages=packages,
            compiled_route_id=self.compiled_route_id,
        )

        # Execute static validators and fixers.
        old_compiled_code = result.regenerate_compiled_code()
        validation_errors.extend(validate_normalize_prisma(result))
        validation_errors.extend(
            await static_code_analysis(result, route_errors_as_todo)
        )
        new_compiled_code = result.get_compiled_code()

        # Auto-fixer works, retry validation (limit to 5 times, to avoid infinite loop)
        if old_compiled_code != new_compiled_code and call_cnt < 5:
            return await self.validate_code(
                packages=packages,
                raw_code=new_compiled_code,
                route_errors_as_todo=route_errors_as_todo,
                raise_validation_error=raise_validation_error,
                call_cnt=call_cnt + 1,
            )

        if validation_errors:
            if raise_validation_error:
                raise ListValidationError("Error validating code", validation_errors)
            else:
                logger.warning("Error validating code: %s", validation_errors)

        return result

    def __validate_main_function(
        self,
        deps_funcs: list[FunctionDef],
        function_code: str,
        validation_errors: list[ValidationError],
    ) -> tuple[str, FunctionDef]:
        """
        Validate the main function body and signature
        Returns:
            tuple[str, FunctionDef]: The function ID and the function object
        """
        # Validate that the main function is implemented.
        func_obj = next((f for f in deps_funcs if f.name == self.func_name), None)
        if not func_obj or not func_obj.is_implemented:
            raise ValidationError(
                f"Main Function body {self.func_name} is not implemented."
                f" Please complete the implementation of this function!"
            )
        func_obj.function_code = function_code

        # Validate that the main function is matching the expected signature.
        func_db: Function | None = self.available_functions.get(self.func_name)
        if not func_db:
            raise AssertionError(f"Function {self.func_name} does not exist on DB")
        try:
            func_obj.validate_matching_function(func_db)
        except Exception as e:
            validation_errors.append(ValidationError(e))

        return func_db.id, func_obj


# ======= Static Code Validation Helper Functions =======#


async def static_code_analysis(
    func: GeneratedFunctionResponse,
    add_todo_on_error: bool,
) -> list[ValidationError]:
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
    validation_errors += await __execute_ruff(func, add_todo_on_error)
    validation_errors += await __execute_pyright(func, add_todo_on_error)

    return validation_errors


async def __execute_ruff(
    func: GeneratedFunctionResponse,
    add_todo_on_error: bool,
) -> list[ValidationError]:
    separator = "#------Code-Start------#"
    code = "\n".join(func.imports + [separator, func.rawCode])
    validation_errors: list[ValidationError] = []

    try:
        # Currently Disabled Rule List
        # E402 module level import not at top of file
        # F841 local variable is assigned to but never used
        code = await exec_external_on_contents(
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
    except ValidationError as e:
        if isinstance(e, ValidationErrorWithContent):
            # Ruff failed, but the code is reformatted
            code = e.content
            e = str(e)

        error_messages = [
            v
            for v in str(e).split("\n")
            if v.strip()
            if re.match(r"Found \d+ errors?\.", v) is None
        ]

        # Append problematic line to the error message or add it as TODO line
        split_pattern = r"(.+):(\d+):(\d+): (.+)"
        for error_message in error_messages:
            error_split = re.match(split_pattern, error_message)

            if not error_split:
                error = ValidationError(error_message)
            else:
                _, line, _, error = error_split.groups()
                error = LineValidationError(error=error, code=code, line_from=int(line))

            if add_todo_on_error:
                code = error.append_error_as_todo(code)
            else:
                validation_errors.append(error)

        if __fix_missing_imports(error_messages, func):
            return validation_errors

    split = code.split(separator)
    func.imports = split[0].splitlines()
    func.rawCode = split[1].strip()

    return validation_errors


async def __execute_pyright(
    func: GeneratedFunctionResponse,
    add_todo_on_error: bool,
) -> list[ValidationError]:
    separator = "#------Code-Start------#"
    code = "\n".join(func.imports + [separator, func.rawCode])
    validation_errors: list[ValidationError] = []

    # Create temporary directory under the TEMP_DIR with random name
    temp_dir = os.path.join(PROJECT_TEMP_DIR, func.compiled_route_id)
    py_path = await setup_if_required(temp_dir, copy_from_parent=True)

    async def __execute_pyright_commands(code: str) -> list[ValidationError]:
        try:
            await execute_command(
                ["pip", "install", "-r", "requirements.txt"], temp_dir, py_path
            )
        except ValidationError as e:
            # Unknown deps should be reported as validation errors
            if add_todo_on_error:
                code = e.append_error_as_todo(code)
            else:
                validation_errors.append(e)

        # run prisma generate
        if func.db_schema:
            await execute_command(["prisma", "generate"], temp_dir, py_path)

        # execute pyright
        result = await execute_command(
            ["pyright", "--outputjson"], temp_dir, py_path, raise_on_error=False
        )
        if not result:
            return []

        try:
            json_response = json.loads(result)["generalDiagnostics"]
        except Exception as e:
            logger.error(f"Error parsing pyright output, error: {e} output: {result}")
            raise e

        for e in json_response:
            rule = e.get("rule", "")
            severity = e.get("severity", "")
            if (
                severity != "error"
                or rule
                in [
                    "reportRedeclaration",
                    "reportArgumentType",  # This breaks prisma query with dict
                ]
                or rule.startswith("reportOptional")  # TODO: improve prompt & enable
            ):
                continue

            e = LineValidationError(
                error=f"{e['message']} [{e.get('rule', '')}]",
                code=code,
                line_from=e["range"]["start"]["line"] + 1,
            )
            if add_todo_on_error:
                code = e.append_error_as_todo(code)
            else:
                validation_errors.append(e)

        # read code from code.py. split the code into imports and raw code
        code = open(f"{temp_dir}/code.py").read()
        split = code.split(separator)
        func.imports = split[0].splitlines()
        func.rawCode = split[1].strip()

        return validation_errors

    packages = "\n".join(
        [str(p) for p in func.packages if p.package_name not in DEFAULT_DEPS]
    )
    with open(f"{temp_dir}/schema.prisma", "w") as p:
        with open(f"{temp_dir}/code.py", "w") as f:
            with open(f"{temp_dir}/requirements.txt", "w") as r:
                # write the requirements to requirements.txt
                r.write(packages)
                r.flush()

                # write the code to code.py
                f.write(code)
                f.flush()

                # write the prisma schema to schema.prisma
                p.write(PRISMA_FILE_HEADER + "\n" + func.db_schema)
                p.flush()

                return await __execute_pyright_commands(code)


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


def __fix_missing_imports(
    errors: list[str], func: GeneratedFunctionResponse
) -> list[str]:
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
    return missing_imports


def validate_normalize_prisma(func: GeneratedFunctionResponse) -> list[ValidationError]:
    """
    Validate and normalize the prisma code in the function
    Args:
        func (GeneratedFunctionResponse):
            The function to validate and normalize.
            compiled code, e.g: `func.rawCode` and `func.imports` will be mutated.
    Returns:
        list[str]: The list validation errors
    """
    validation_errors: list[str] = []
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
        renamed_code = re.sub(pattern, new_name, code)
        # Avoid renaming class names
        renamed_code = renamed_code.replace(f"class {new_name}", f"class {old_name}")
        return renamed_code

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
    if "prisma.enums" in code:
        imports.append("import prisma.enums")
    if "prisma.models" in code:
        imports.append("import prisma.models")
    if "prisma.errors" in code:
        imports.append("import prisma.errors")

    # Sometimes it does this, it's not a valid import
    if "from pydantic import Optional" in imports:
        imports.remove("from pydantic import Optional")

    imports = sorted({i.strip() for i in imports})

    func.imports, func.rawCode = imports, code

    return [ValidationError(e) for e in validation_errors]
