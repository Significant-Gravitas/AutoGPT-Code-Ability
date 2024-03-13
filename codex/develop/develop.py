import ast
import logging
from typing import List

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
    ObjectFieldModel,
    ObjectTypeModel,
    create_object_type,
    get_typing_imports,
    is_type_equal,
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
        if node.name in ["__init__", "__repr__"]:
            self.generic_visit(node)
            return

        args = []
        for arg in node.args.args:
            arg_type = ast.unparse(arg.annotation) if arg.annotation else "object"
            args.append((arg.arg, arg_type))
        return_type = ast.unparse(node.returns) if node.returns else None

        # Raise validation error on nested functions
        if any(isinstance(v, ast.FunctionDef) for v in node.body):
            raise ValidationError(
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
        node.body = template_body
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

        fields = []
        for v in node.body:
            if isinstance(v, ast.AnnAssign):
                field = ObjectFieldModel(
                    name=ast.unparse(v.target),
                    description=ast.unparse(v.annotation),
                    type=ast.unparse(v.annotation),
                    value=ast.unparse(v.value) if v.value else None,
                )
            elif isinstance(v, ast.Assign):
                if len(v.targets) > 1:
                    raise ValidationError(
                        f"Class {node.name} has multiple assignments in a single line."
                    )
                field = ObjectFieldModel(
                    name=ast.unparse(v.targets[0]),
                    description=ast.unparse(v.targets[0]),
                    type=type(ast.unparse(v.value)).__name__,
                    value=ast.unparse(v.value) if v.value else None,
                )
            else:
                continue
            fields.append(field)

        self.objects[node.name] = ObjectTypeModel(
            name=node.name,
            code=ast.unparse(node),
            description=doc_string,
            Fields=fields,
            is_pydantic=is_pydantic,
            is_enum=is_enum,
            is_implemented=is_implemented,
        )

        if not is_implemented:
            raise ValidationError(
                f"Class {node.name} is not implemented. "
                f"Please complete the implementation of this class!"
            )

        self.generic_visit(node)

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

    if any(
        [
            x[0] != y[0] or not is_type_equal(x[1], y[1])
            # TODO: remove sorted and provide a stable order for one-to-many arg-types.
            for x, y in zip(sorted(expected_args), sorted(requested_func.arg_types))
        ]
    ):
        raise ValidationError(
            f"Function {func_name} has different arguments than expected, expected {expected_args} but got {requested_func.arg_types}"
        )
    if not is_type_equal(expected_rets, requested_func.return_type):
        raise ValidationError(
            f"Function {func_name} has different return type than expected, expected {expected_rets} but got {requested_func.return_type}"
        )


def static_code_analysis(func: GeneratedFunctionResponse) -> str:
    imports = func.imports.copy()
    for obj in func.available_objects.values():
        imports.extend(obj.importStatements)
    imports_code = "\n".join(sorted(set(imports)))

    template_code = "\n\n".join(
        [
            generate_object_template(obj, noqa=True, stub=True)
            for obj in func.available_objects.values()
        ]
    )

    objects_code = "\n\n".join(
        [
            generate_object_template(obj, noqa=True, stub=False)
            for obj in func.available_objects.values()
        ]
        + [
            obj.code
            for obj in func.objects.values()
            if obj.name not in func.available_objects
        ]
    )

    functions_code = "\n\n".join(
        [func.function_code for func in func.functions.values()]
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

    return exec_external_on_contents(
        command_arguments=["ruff", "check", "--fix"], file_contents=code, suffix=".py"
    ).split(separator, maxsplit=1)[1]


class DevelopAIBlock(AIBlock):
    developement_phase: DevelopmentPhase = DevelopmentPhase.DEVELOPMENT
    prompt_template_name = "develop"
    model = "gpt-4-0125-preview"
    langauge = "python"

    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        try:
            text = response.response

            requirment_blocks = text.split("```requirements")
            requirment_blocks.pop(0)
            if len(requirment_blocks) != 1:
                packages = []
            else:
                packages: List[Package] = parse_requirements(
                    requirment_blocks[0].split("```")[0]
                )

            code_blocks = text.split("```python")
            code_blocks.pop(0)
            if len(code_blocks) != 1:
                raise ValidationError(
                    f"There are {len(code_blocks)} code blocks in the response. "
                    + "There should be exactly 1"
                )
            code = code_blocks[0].split("```")[0]

            if (".connect()" in code) or ("async with Prisma() as db:" in code):
                raise ValidationError(
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
                raise ValidationError(
                    "There is no need to do `from prisma import Prisma` as we are using the prisma.models to access the database."
                )

            if ("prisma.errors." in code) and ("import prisma.errors" not in code):
                raise ValidationError(
                    "You are using prisma.errors but not importing it. Please add `import prisma.errors` at the top of the code."
                )

            try:
                tree = ast.parse(code)
                visitor = FunctionVisitor()
                visitor.visit(tree)
            except Exception as e:
                # Important: ValidationErrors are used in the retry prompt
                raise ValidationError(f"Error parsing code: {e}")

            func_name = invoke_params["function_name"]
            if func_name not in visitor.functions:
                # Important: ValidationErrors are used in the retry prompt
                raise ValidationError(f"Function {func_name} not found in code")

            requested_func = visitor.functions.get(invoke_params["function_name"])
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
            validate_matching_function(expected_func, requested_func)

            functions = visitor.functions.copy()
            del functions[func_name]

            expected_types = []
            if expected_func.FunctionArgs:
                expected_types.extend([v.typeName for v in expected_func.FunctionArgs])
            if expected_func.FunctionReturn:
                expected_types.append(expected_func.FunctionReturn.typeName)
            imports = set(visitor.imports + get_typing_imports(expected_types))

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
                template=requested_func.function_template,
                functionCode=function_code,
                functions=functions,
            )
            result.functionCode = static_code_analysis(result)
            response.response = result

            return response
        except Exception as e:
            # Important: ValidationErrors are used in the retry prompt
            raise ValidationError(f"Error validating response: {e}")

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

        available_objects = generated_response.available_objects
        for obj in generated_response.objects.values():
            available_objects = await create_object_type(obj, available_objects)

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
