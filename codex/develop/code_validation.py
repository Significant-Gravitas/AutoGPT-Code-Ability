import ast
import collections
import datetime
import json
import logging
import pathlib
import re
import typing
import uuid

import black
import isort
import prisma
from prisma.models import Function, ObjectType

from codex.common.ai_block import (
    TODO_COMMENT,
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
                # This should happen only on `reformat_code` call
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


CODE_SEPARATOR = "#------Code-Start------#"


def __pack_import_and_function_code(func: GeneratedFunctionResponse) -> str:
    return "\n".join(func.imports + [CODE_SEPARATOR, func.rawCode])


def __unpack_import_and_function_code(code: str) -> tuple[list[str], str]:
    split = code.split(CODE_SEPARATOR)
    return split[0].splitlines(), split[1].strip()


async def __execute_ruff(
    func: GeneratedFunctionResponse,
    add_todo_on_error: bool,
) -> list[ValidationError]:
    code = __pack_import_and_function_code(func)

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
        func.imports, func.rawCode = __unpack_import_and_function_code(code)
        return []

    except ValidationError as e:
        if isinstance(e, ValidationErrorWithContent):
            # Ruff failed, but the code is reformatted
            code = e.content
            e = str(e)

        error_messages = [
            v
            for v in str(e).split("\n")
            if v.strip()
            if re.match(r"Found \d+ errors?\.*", v) is None
        ]

        added_imports, error_messages = __fix_missing_imports(error_messages, func)

        # Append problematic line to the error message or add it as TODO line
        validation_errors: list[ValidationError] = []
        split_pattern = r"(.+):(\d+):(\d+): (.+)"
        for error_message in error_messages:
            error_split = re.match(split_pattern, error_message)

            if not error_split:
                error = ValidationError(error_message)
            else:
                _, line, _, error = error_split.groups()
                error = LineValidationError(error=error, code=code, line_from=int(line))

            validation_errors.append(error)

        if add_todo_on_error:
            code = append_errors_as_todos(validation_errors, code)
            validation_errors.clear()

        func.imports, func.rawCode = __unpack_import_and_function_code(code)
        func.imports.extend(added_imports)  # Avoid line-code change, do it at the end.

        return validation_errors


def append_errors_as_todos(errors: list[ValidationError], code: str) -> str:
    """
    Append the errors as TODO comments in the code
    Args:
        errors (list[ValidationError]): The list of errors
        code (str): The code snippet
    Returns:
        str: The code snippet with the errors appended as TODO comments
    """

    line_validation_errors: list[LineValidationError] = []
    non_line_validation_errors: list[ValidationError] = []
    for error in errors:
        if isinstance(error, LineValidationError):
            line_validation_errors.append(error)
        else:
            non_line_validation_errors.append(error)

    replaced_error_messages: dict[str, str] = {}

    # Start with line-errors, to avoid changing the line numbers
    for err in line_validation_errors:
        code_lines = code.split("\n")
        if err.line_from > len(code_lines):
            continue

        error_uid: str = uuid.uuid4().hex
        error_msg: str = super(ValidationError, err).__str__().replace("\n", "\n#   ")

        index = err.line_from - 1
        if TODO_COMMENT not in code_lines[index]:
            code_lines[index] = f"{code_lines[index]} {TODO_COMMENT} {error_uid}"

        replaced_error_messages[error_uid] = error_msg
        code = "\n".join(code_lines)

    # Append non-line errors at the initial code
    for err in non_line_validation_errors:
        error_uid: str = uuid.uuid4().hex
        error_msg: str = err.__str__().replace("\n", "\n#     ")
        code = f"{TODO_COMMENT} {error_uid}\n{code}"
        replaced_error_messages[error_uid] = error_msg

    # Replace error_uid with the actual error message
    for uid, msg in replaced_error_messages.items():
        code = code.replace(uid, msg)

    return code


async def __execute_pyright(
    func: GeneratedFunctionResponse,
    add_todo_on_error: bool,
) -> list[ValidationError]:
    code = __pack_import_and_function_code(func)
    validation_errors: list[ValidationError] = []

    # Create temporary directory under the TEMP_DIR with random name
    temp_dir = PROJECT_TEMP_DIR / func.compiled_route_id
    py_path = await setup_if_required(temp_dir)

    async def __execute_pyright_commands(code: str) -> list[ValidationError]:
        try:
            await execute_command(
                ["pip", "install", "-r", "requirements.txt"], temp_dir, py_path
            )
        except ValidationError as e:
            # Unknown deps should be reported as validation errors
            if add_todo_on_error:
                code = append_errors_as_todos([e], code)
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
            rule: str = e.get("rule", "")
            severity: str = e.get("severity", "")
            excluded_rules = ["reportMissingImports"] if add_todo_on_error else []
            if (
                severity != "error"
                or rule
                in [
                    "reportRedeclaration",
                    "reportArgumentType",  # This breaks prisma query with dict
                ]
                + excluded_rules
                or rule.startswith("reportOptional")  # TODO: improve prompt & enable
            ):
                continue

            # Grab any enhancements we can for the error
            error_message: str = f"{e['message']}. {e.get('rule', '')}"
            if error_enhancements := await get_error_enhancements(
                rule,
                error_message,
                py_path,
            ):
                error_message += f"\n{error_enhancements}"

            e = LineValidationError(
                error=error_message,
                code=code,
                line_from=e["range"]["start"]["line"] + 1,
            )
            validation_errors.append(e)

        # read code from code.py. split the code into imports and raw code
        code = open(f"{temp_dir}/code.py").read()
        if add_todo_on_error:
            code = append_errors_as_todos(validation_errors, code)
            validation_errors.clear()

        func.imports, func.rawCode = __unpack_import_and_function_code(code)

        return validation_errors

    packages = "\n".join(
        [str(p) for p in func.packages if p.package_name not in DEFAULT_DEPS]
    )
    (temp_dir / "requirements.txt").write_text(packages)
    (temp_dir / "code.py").write_text(code)
    (temp_dir / "schema.prisma").write_text(PRISMA_FILE_HEADER + "\n" + func.db_schema)

    return await __execute_pyright_commands(code)


async def find_module_dist_and_source(
    module: str, py_path: pathlib.Path | str
) -> typing.Tuple[pathlib.Path | None, pathlib.Path | None]:
    # Find the module in the env
    modules_path = pathlib.Path(py_path).parent / "lib" / "python3.11" / "site-packages"
    matches = modules_path.glob(f"{module}*")

    # resolve the generator to an array
    matches = list(matches)
    if not matches:
        return None, None

    # find the dist info path and the module path
    dist_info_path: typing.Optional[pathlib.Path] = None
    module_path: typing.Optional[pathlib.Path] = None

    # find the dist info and the module path
    # TODO(ntindle): This is a naive implementation, we should improve this as pydantic and pydantic-core would match and its a crapshoot which one we get
    for match in matches:
        if ".dist-info" in match.name:
            dist_info_path = match
            break
    for match in matches:
        if module in match.name:
            module_path = match
            break

    # We couldn't find the module
    if not dist_info_path or not module_path:
        return None, None

    return dist_info_path, module_path


async def get_error_enhancements(
    rule: str,
    error_message: str,
    py_path: str,
) -> str | None:
    # python match the rule and error message to a case
    match rule:
        case "reportAttributeAccessIssue":
            if "is not a known member of module" in error_message:
                logger.info(f"Attempting to enhance error: {error_message}")

                # Extract the attempted attribute and the module
                # attempted_attribute = (
                #     error_message.split("is not a known member of module")[0]
                #     .strip()
                #     .replace('"', "")
                # )
                # Split out ' "module". reportAttributeAccessIssue ' from the error message
                module = (
                    error_message.split("is not a known member of module")[1]
                    .split(". reportAttributeAccessIssue")[0]
                    .strip()
                    .replace('"', "")
                )

                # Find the dist info and the module path
                dist_info_path: typing.Optional[pathlib.Path] = None
                module_path: typing.Optional[pathlib.Path] = None
                dist_info_path, module_path = await find_module_dist_and_source(
                    module, py_path
                )

                # Return if we can't find the dist info or the module path
                if not dist_info_path and not module_path:
                    logger.info(f"Could not enhance error: {error_message}")
                    return None

                # Find the metadata and the matching context
                metadata_contents: typing.Optional[str] = None
                matching_context: typing.Optional[str] = None

                # Read the dist info's METADATA file
                if dist_info_path:
                    # Find the dist info's METADATA file
                    metadata_file = dist_info_path / "METADATA"
                    if metadata_file.exists():
                        metadata_contents = metadata_file.read_text()

                # Find the module's nearest matching attempted attribute in the module folder using treesitter
                # TODO(ntindle): Implement this
                if not metadata_contents and not matching_context:
                    logger.info(f"Could not enhance error: {error_message}")
                    return None

                return f"Found Metadata for the module: {metadata_contents}"
        case _:
            pass
    return None


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
) -> tuple[set[str], list[str]]:
    """
    Generate missing imports based on the errors
    Args:
        errors (list[str]): The list of errors
        func (GeneratedFunctionResponse): The function to fix the imports
    Returns:
        tuple[set[str], list[str]]: The set of missing imports and the list of non-missing import errors
    """
    # parse "model X {" and "enum X {" from func.db_schema
    schema_imports = {}
    for entity in ["model", "enum"]:
        pattern = f"{entity}\\s+([a-zA-Z0-9_]+)\\s+{{"
        matches = re.findall(pattern, func.db_schema)
        for match in matches:
            schema_imports[match] = f"from prisma.{entity}s import {match}"

    missing_imports = []
    filtered_errors = []
    for error in errors:
        pattern = r"Undefined name `(.+?)`"
        match = re.search(pattern, error)
        if not match:
            filtered_errors.append(error)
            continue

        missing_type = match.group(1)
        if missing_type in schema_imports:
            missing_imports.append(schema_imports[missing_type])
        elif missing_type in AUTO_IMPORT_TYPES:
            missing_imports.append(AUTO_IMPORT_TYPES[missing_type])
        else:
            filtered_errors.append(error)

    return set(missing_imports), filtered_errors


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
