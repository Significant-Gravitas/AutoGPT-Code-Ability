import ast
import logging
from importlib.metadata import packages_distributions
from typing import List

from prisma.enums import DevelopmentPhase, FunctionState
from prisma.models import Function
from prisma.types import (
    FunctionCreateInput,
    FunctionCreateWithoutRelationsInput,
    FunctionUpdateInput,
    PackageCreateWithoutRelationsInput,
)

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
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
        self.functions = {}
        self.imports = []

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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = []
        for arg in node.args.args:
            arg_type = ast.unparse(arg.annotation) if arg.annotation else "Unknown"
            args.append(arg_type)
        args_str = ", ".join(args)
        return_type = ast.unparse(node.returns) if node.returns else "Unknown"

        # Extracting the docstring if it exists
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            doc_string = node.body[0].value.s  # .s to get the string content
        else:
            doc_string = ""  # Or set a default docstring value if you prefer
        self.functions[node.name] = FunctionDef(
            name=node.name,
            doc_string=doc_string,
            args=args_str,
            return_type=return_type,
            function_template=ast.unparse(node),
        )
        self.generic_visit(node)


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
                raise ValidationError(
                    f"There are {len(requirment_blocks)} requirements blocks in the"
                    + " response. There should be exactly 1"
                )

            packages = parse_requirements(requirment_blocks[0].split("```")[0])

            code_blocks = text.split("```python")
            code_blocks.pop(0)
            if len(code_blocks) != 1:
                raise ValidationError(
                    f"There are {len(code_blocks)} code blocks in the response. "
                    + "There should be exactly 1"
                )
            code = code_blocks[0].split("```")[0]

            try:
                tree = ast.parse(code)
                visitor = FunctionVisitor()
                visitor.visit(tree)
            except Exception as e:
                raise ValidationError(f"Error parsing code: {e}")

            assert (
                invoke_params["function_name"] in visitor.functions
            ), f"Function {invoke_params['function_name']} not found in code"

            assert (
                "pass" not in visitor.functions[invoke_params["function_name"]]
            ), "Function body is empty"

            functions = visitor.functions.copy()
            del functions[invoke_params["function_name"]]

            response.response = GeneratedFunctionResponse(
                function_id=invoke_params["function_id"]
                if "function_id" in invoke_params
                else None,
                function_name=invoke_params["function_name"],
                api_route_spec=invoke_params["api_route"],
                template=invoke_params["description"],
                rawCode=code,
                packages=packages,
                imports=visitor.imports,
                functionCode=visitor.functions[
                    invoke_params["function_name"]
                ].function_template,
                functions=functions,
            )
            return response
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """This is just a temporary that doesnt have a database model"""
        generated_response: GeneratedFunctionResponse = validated_response.response
        if generated_response.function_id:
            # Detect if the function already exists and update it
            return await self.update_item(ids, validated_response)
        else:
            try:
                generated_response: GeneratedFunctionResponse = (
                    validated_response.response
                )
                function_defs: list[FunctionCreateWithoutRelationsInput] = []
                if generated_response.functions:
                    for key, value in generated_response.functions.items():
                        model = FunctionCreateWithoutRelationsInput(
                            functionName=value.name,
                            template=value.function_template,
                            state=FunctionState.DEFINITION,
                        )

                        function_defs.append(model)

                logger.info(f"Child Functions Detected: {len(function_defs)}")

                create_input = FunctionCreateInput(
                    functionName=generated_response.function_name,
                    template=generated_response.template,
                    state=FunctionState.WRITTEN,
                    Packages={
                        "create": [
                            PackageCreateWithoutRelationsInput(**p.model_dump())
                            for p in generated_response.packages
                        ]
                    },
                    rawCode=generated_response.rawCode,
                    importStatements=generated_response.imports,
                    functionCode=generated_response.functionCode,
                    ChildFunction={"create": function_defs},
                    ApiRouteSpec={
                        "connect": {"id": generated_response.api_route_spec.id}
                    },
                )
                if generated_response.api_route_spec.DatabaseSchema:
                    create_input["DatabaseSchema"] = {
                        "connect": {
                            "id": generated_response.api_route_spec.DatabaseSchema.id
                        }
                    }

                # Child Functions Must be created without relations
                # Here we add the relations after the function is created
                func = await Function.prisma().create(data=create_input)
                if func.ChildFunction:
                    for function_def in func.ChildFunction:
                        await Function.prisma().update(
                            where={"id": function_def.id},
                            data={
                                "ApiRouteSpec": {
                                    "connect": {
                                        "id": generated_response.api_route_spec.id
                                    }
                                }
                            },
                        )
                # We need to reload from the database the child functions so they 
                # have the api route spec attached
                func = await Function.prisma().find_unique_or_raise(
                    where={"id": func.id},
                    include={
                        "ParentFunction": True,
                        "ChildFunction": {"include": {"ApiRouteSpec": True}},
                    },
                )
                logger.info(
                    f"✅ Created Function. Child Functions: {len(function_defs)}/{len(func.ChildFunction if func.ChildFunction else [])}"
                )
                return func
            except Exception as e:
                logger.info(f"Error saving Function: {e}")

    async def update_item(  # type: ignore
        self, ids: Identifiers, validated_response: ValidatedResponse
    ) -> Function:  # type: ignore
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

        function_defs = []

        generated_response: GeneratedFunctionResponse = validated_response.response
        function_defs: list[FunctionCreateWithoutRelationsInput] = []
        if generated_response.functions:
            for key, value in generated_response.functions.items():
                model = FunctionCreateWithoutRelationsInput(
                    functionName=value.name,
                    template=value.function_template,
                    state=FunctionState.DEFINITION,
                )

                function_defs.append(model)

        update_obj = FunctionUpdateInput(
            state=FunctionState.WRITTEN,
            Packages={
                "create": [
                    PackageCreateWithoutRelationsInput(**p.model_dump())
                    for p in generated_response.packages
                ]
            },
            rawCode=generated_response.rawCode,
            importStatements=generated_response.imports,
            functionCode=generated_response.functionCode,
            ChildFunction={"create": function_defs},
        )

        if not generated_response.function_id:
            raise AssertionError("Function ID is required to update")

        func: Function | None = await Function.prisma().update(
            where={"id": generated_response.function_id}, data=update_obj
        )

        if not func:
            raise AssertionError(
                f"Function with id {generated_response.function_id} not found"
            )
        logger.info(f"✅ Updated Function")

        return func
