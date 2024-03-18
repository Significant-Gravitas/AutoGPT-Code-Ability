import ast
import collections
import datetime
import logging
import re
import typing
from typing import Iterable, List

import prisma
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
from codex.common.exec_external_tool import exec_external_on_contents
from codex.common.model import (
    PYTHON_TYPES,
    ObjectFieldModel,
    ObjectTypeModel,
    create_object_type,
    is_type_equal,
    normalize_type,
)
from codex.develop.compile import ComplicationFailure
from codex.develop.function import construct_function, generate_object_template
from codex.develop.model import FunctionDef, GeneratedFunctionResponse, Package

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


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: dict[str, FunctionDef] = {}
        self.objects: dict[str, ObjectTypeModel] = {}
        self.imports: list[str] = []
        self.globals: list[str] = []
        self.errors: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            import_line = f"import {alias.name}"
            if alias.asname:
                import_line += f" as {alias.asname}"
            self.imports.append(import_line)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            import_line = f"from {node.module} import {alias.name}"
            if alias.asname:
                import_line += f" as {alias.asname}"
            self.imports.append(import_line)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # treat async functions as normal functions
        self.visit_FunctionDef(node)  # type: ignore

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = []
        for arg in node.args.args:
            arg_type = ast.unparse(arg.annotation) if arg.annotation else "object"
            args.append((arg.arg, normalize_type(arg_type)))
        return_type = (
            normalize_type(ast.unparse(node.returns)) if node.returns else None
        )

        # Raise validation error on nested functions
        if any(isinstance(v, ast.FunctionDef) for v in node.body):
            self.errors.append(
                "Nested functions are not allowed in the code: " + node.name
            )

        # Extract doc_string & function body
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            doc_string = ast.unparse(node.body[0])
            template_body = [node.body[0], ast.Pass()]
            is_implemented = not isinstance(node.body[1], ast.Pass)
        else:
            doc_string = ""
            template_body = [ast.Pass()]
            is_implemented = not isinstance(node.body[0], ast.Pass)

        # Construct function template
        original_body = node.body.copy()
        node.body = template_body  # type: ignore
        function_template = ast.unparse(node)
        node.body = original_body

        self.functions[node.name] = FunctionDef(
            name=node.name,
            arg_types=args,
            arg_descs={},  # TODO: Extract out Args and Returns from doc_string
            return_type=return_type,
            return_desc="",  # TODO: Extract out Args and Returns from doc_string
            is_implemented=is_implemented,
            function_desc=doc_string,  # TODO: Exclude Args and Returns from doc_string,
            function_template=function_template,
            function_code=ast.unparse(node),
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visits a ClassDef node in the AST and checks if it is a Pydantic class.
        If it is a Pydantic class, adds its name to the list of Pydantic classes.
        """
        is_pydantic = any(
            [
                (isinstance(base, ast.Name) and base.id == "BaseModel")
                or (isinstance(base, ast.Attribute) and base.attr == "BaseModel")
                for base in node.bases
            ]
        )
        is_enum = any(
            [
                (isinstance(base, ast.Name) and base.id.endswith("Enum"))
                or (isinstance(base, ast.Attribute) and base.attr.endswith("Enum"))
                for base in node.bases
            ]
        )
        is_implemented = not any(isinstance(v, ast.Pass) for v in node.body)
        doc_string = ""
        if node.body and isinstance(node.body[0], ast.Expr):
            doc_string = ast.unparse(node.body[0])

        if node.name in PYTHON_TYPES:
            self.errors.append(
                f"Can't declare class with a Python built-in name "
                f"`{node.name}`. Please use a different name."
            )

        fields = []
        methods = []
        for v in node.body:
            if isinstance(v, ast.AnnAssign):
                field = ObjectFieldModel(
                    name=ast.unparse(v.target),
                    type=ast.unparse(v.annotation),
                    value=ast.unparse(v.value) if v.value else None,
                )
            elif isinstance(v, ast.Assign):
                if len(v.targets) > 1:
                    self.errors.append(
                        f"Class {node.name} has multiple assignments in a single line."
                    )
                field = ObjectFieldModel(
                    name=ast.unparse(v.targets[0]),
                    type=type(ast.unparse(v.value)).__name__,
                    value=ast.unparse(v.value) if v.value else None,
                )
            else:
                methods.append(ast.unparse(v))
                continue
            fields.append(field)

        self.objects[node.name] = ObjectTypeModel(
            name=node.name,
            code="\n".join(methods),
            description=doc_string,
            Fields=fields,
            is_pydantic=is_pydantic,
            is_enum=is_enum,
            is_implemented=is_implemented,
        )

        """Some class are simply used as a type and doesn't have any new fields"""
        # if not is_implemented:
        #     raise ValidationError(
        #         f"Class {node.name} is not implemented. "
        #         f"Please complete the implementation of this class!"
        #     )

    def visit(self, node):
        if (
            isinstance(node, ast.Assign)
            or isinstance(node, ast.AnnAssign)
            or isinstance(node, ast.AugAssign)
        ) and node.col_offset == 0:
            self.globals.append(ast.unparse(node))
        super().visit(node)


def validate_matching_function(existing_func: Function, requested_func: FunctionDef):
    expected_args = [(f.name, f.typeName) for f in existing_func.FunctionArgs or []]
    expected_rets = (
        existing_func.FunctionReturn.typeName if existing_func.FunctionReturn else None
    )
    func_name = existing_func.functionName
    errors = []

    if any(
        [
            x[0] != y[0] or not is_type_equal(x[1], y[1]) and x[1] != "object"
            # TODO: remove sorted and provide a stable order for one-to-many arg-types.
            for x, y in zip(sorted(expected_args), sorted(requested_func.arg_types))
        ]
    ):
        errors.append(
            f"Function {func_name} has different arguments than expected, expected {expected_args} but got {requested_func.arg_types}"
        )
    if (
        not is_type_equal(expected_rets, requested_func.return_type)
        and expected_rets != "object"
    ):
        errors.append(
            f"Function {func_name} has different return type than expected, expected {expected_rets} but got {requested_func.return_type}"
        )

    if errors:
        raise ValidationError("Signature validation errors:\n  " + "\n  ".join(errors))


def static_code_analysis(func: GeneratedFunctionResponse):
    """
    Runs static code analysis on the function code and returns the fixed code.
    Args:
        func (GeneratedFunctionResponse): The function to run static code analysis on.
        The attributes of this object will be mutated.
    Raises:
        ValidationError: If the function code has static code analysis errors.
    """
    imports = func.imports.copy()
    imports.append("from enum import Enum")
    # logger.info(f"Imports: {imports}")
    for obj in func.available_objects.values():
        imports.extend(obj.importStatements)

    imports_code = "\n".join(sorted(set([i.strip() for i in imports])))

    # logger.info(f"Imports Code: {imports_code}  ")

    def generate_stub(name, is_enum):
        if is_enum:
            return f"class {name}(Enum):\n    pass"
        else:
            return f"class {name}(BaseModel):\n    pass"

    template_code = "\n\n".join(
        [generate_stub(obj.name, obj.isEnum) for obj in func.available_objects.values()]
        + [
            generate_stub(obj.name, obj.is_enum)
            for obj in func.objects.values()
            if obj.name not in func.available_objects
        ]
    )

    def append_no_qa(code_block: str) -> str:
        lines = code_block.split("\n")
        lines[0] = lines[0] + " # noqa"
        return "\n".join(lines)

    objects_code = "\n\n".join(
        [
            append_no_qa(generate_object_template(obj))
            for obj in func.available_objects.values()
        ]
        + [
            append_no_qa(obj.code)
            for obj in func.objects.values()
            if obj.code and obj.name not in func.available_objects
        ]
    )

    functions_code = "\n\n".join(
        [
            f.template
            for f in func.available_functions.values()
            if f.functionName != func.function_name
        ]
        + [
            f.function_code
            for f in func.functions.values()
            if f.name not in func.available_functions
        ]
    )

    separator = "#==FunctionCode==#"
    code = (
        imports_code
        + "\n\n"
        + template_code
        + "\n\n"
        + objects_code
        + "\n\n"
        + functions_code
        + "\n\n"
        + separator
        + "\n"
        + func.functionCode
    )

    try:
        # E402 module level import not at top of file
        # F841 local variable is assigned to but never used
        func.functionCode = exec_external_on_contents(
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
        ).split(separator, maxsplit=1)[1]
    except ValidationError as e:
        validation_errors = str(e).split("\n")
        if fix_missing_imports(validation_errors, func):
            # Try to fix the missing import and try again.
            return static_code_analysis(func)
        raise e


AUTO_IMPORT_TYPES: dict[str, str] = {"prisma": "import prisma"}
for t in typing.__all__:
    AUTO_IMPORT_TYPES[t] = f"from typing import {t}"
for t in prisma.errors.__all__:
    AUTO_IMPORT_TYPES[t] = f"from prisma.errors import {t}"
for t in datetime.__all__:
    AUTO_IMPORT_TYPES[t] = f"from datetime import {t}"
for t in collections.__all__:
    AUTO_IMPORT_TYPES[t] = f"from collections import {t}"


def fix_missing_imports(errors: list[str], func: GeneratedFunctionResponse) -> bool:
    """
    Fixes missing import errors in the function code.
    Args:
        errors (list[str]): The errors from the static code analysis.
        func (GeneratedFunctionResponse): The function to fix the errors in.
    Returns:
        bool: True if there are imports being added, False for otherwise
    """

    # parse "model X {" and "enum X {" from func.db_schema
    schema_imports = {}
    for entity in ["model", "enum"]:
        pattern = f"{entity} ([a-zA-Z0-9_]+) {{"
        matches = re.findall(pattern, func.db_schema)
        for match in matches:
            schema_imports[match] = f"from prisma.{entity}s import {match}"

    missing_imports = []
    for error in errors:
        # Format: 'Undefined name `X`', parse X and see if X inside
        pattern = r"Undefined name `(.+?)`"
        match = re.search(pattern, error)
        if not match:
            continue

        missing_type = match.group(1)
        if missing_type in schema_imports:
            missing_imports.append(schema_imports[missing_type])
        elif missing_type in AUTO_IMPORT_TYPES:
            missing_imports.append(AUTO_IMPORT_TYPES[missing_type])

    if not missing_imports:
        return False

    func.imports = sorted(set(func.imports + list(missing_imports)))
    return True


def validate_normalize_prisma_code(
    db_schema: str, imports: list[str], code: str
) -> tuple[list[str], str]:
    """
    Validates and normalizes the prisma code.
    Args:
        imports (list[str]): List of import statements.
        code (str): The code to be validated and normalized.
    Returns:
        list[str]: List of normalized import statements.
        str: Normalized code.
    Raises:
        ValidationError: If the prisma usage in the code is not valid.
    """
    validation_errors = []

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
            if f"from prisma.{entity}s import" in import_statement:
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
            if f"{entity} {name} " not in db_schema:
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
    if validation_errors:
        raise ValidationError(validation_errors)

    return imports, code


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
            # logger.warning(f"RAW RESPONSE:\n\n{text}")
            requirement_blocks = text.split("```requirements")
            requirement_blocks.pop(0)
            if len(requirement_blocks) != 1:
                packages = []
            else:
                packages: List[Package] = parse_requirements(
                    requirement_blocks[0].split("```")[0]
                )

            code_blocks = text.split("```python")
            code_blocks.pop(0)
            if len(code_blocks) != 1:
                error = (
                    f"There are {len(code_blocks)} code blocks in the response. "
                    + "There should be exactly 1"
                )
                if len(code_blocks) == 0:
                    raise ValidationError("No code blocks found in the response")
                else:
                    validation_errors.append(error)

            code = code_blocks[0].split("```")[0]

            try:
                tree = ast.parse(code)
                visitor = FunctionVisitor()
                visitor.visit(tree)
                validation_errors.extend(visitor.errors)
            except Exception as e:
                # Important: ValidationErrors are used in the retry prompt
                raise ValidationError(f"Error parsing code: {e}")

            func_name = invoke_params["function_name"]
            requested_func = visitor.functions.get(func_name)
            # TODO: Can we add this to the validation_errors list too
            if not requested_func or not requested_func.is_implemented:
                raise ValidationError(
                    f"Main Function body {func_name} is not implemented."
                    f" Please complete the implementation of this function!"
                )
            function_code = (
                "\n".join(visitor.globals) + "\n\n" + requested_func.function_code
            )

            # Validate the requested_func.args and requested_func.returns to the invoke_params
            expected_func: Function = invoke_params["available_functions"].get(
                func_name
            )
            if not expected_func:
                raise ComplicationFailure(
                    f"Function {func_name} signature not available"
                )
            try:
                validate_matching_function(expected_func, requested_func)
            except ValidationError as e:
                validation_errors.append(str(e))

            functions = visitor.functions.copy()
            del functions[func_name]
            imports = visitor.imports.copy()
            db_schema = invoke_params.get("database_schema", "")

            try:
                imports, function_code = validate_normalize_prisma_code(
                    db_schema, imports, function_code
                )
            except ValidationError as errors:
                if isinstance(errors, Iterable):
                    validation_errors.extend(errors)
                else:
                    validation_errors.append(str(errors))

            already_declared_entities = set(
                [
                    obj.name
                    for obj in visitor.objects.values()
                    if obj.name in invoke_params["available_objects"].keys()
                ]
                + [
                    func.name
                    for func in visitor.functions.values()
                    if func.name in invoke_params["available_functions"].keys()
                ]
            )
            if not already_declared_entities:
                validation_errors.append(
                    "These class/function names has already been declared in the code, "
                    "no need to declare them again: "
                    + ", ".join(already_declared_entities)
                )

            result = GeneratedFunctionResponse(
                function_id=expected_func.id,
                function_name=expected_func.functionName,
                compiled_route_id=invoke_params["compiled_route_id"],
                available_objects=invoke_params["available_objects"],
                available_functions=invoke_params["available_functions"],
                rawCode=code,
                packages=packages,
                imports=sorted(imports),
                objects=visitor.objects,
                template=requested_func.function_template or "",
                functionCode=function_code,
                functions=functions,
                db_schema=db_schema,
            )
            try:
                static_code_analysis(result)
            except ValidationError as e:
                validation_errors.append(str(e))

            response.response = result

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
                    validate_matching_function(same_func, function)
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
            ChildFunctions={"create": function_defs},
        )

        if not generated_response.function_id:
            raise AssertionError("Function ID is required to update")

        func: Function | None = await Function.prisma().update(
            where={"id": generated_response.function_id},
            data=update_obj,
            include={
                **INCLUDE_FUNC["include"],
                "ParentFunction": INCLUDE_FUNC,
                "ChildFunctions": INCLUDE_FUNC,
            },
        )
        if not func:
            raise AssertionError(
                f"Function with id {generated_response.function_id} not found"
            )

        logger.info(f"✅ Updated Function: {func.functionName} - {func.id}")

        return func
