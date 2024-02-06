import ast

from prisma.models import CodeGraph as CodeGraphDBModel

from codex.architect.model import CodeGraph, FunctionDef
from codex.common.ai_block import AIBlock, ValidatedResponse, ValidationError


class CodeGraphVisitor(ast.NodeVisitor):
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


class CodeGraphAIBlock(AIBlock):
    
    prompt_template_name = "codegraph/cg.python"
    model = "gpt-4-0125-preview"
    langauge = "python"
    
    def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        try:
            text = response.response
            code = text.split("```python")[1].split("```")[0]

            tree = ast.parse(code)
            visitor = CodeGraphVisitor()
            visitor.visit(tree)

            functions = visitor.functions.copy()
            del functions[invoke_params["function_name"]]

            response.response = CodeGraph(
                function_name=invoke_params["function_name"],
                api_route=invoke_params["api_route"],
                code_graph=visitor.functions[
                    invoke_params["function_name"]
                ].function_template,
                imports=visitor.imports,
                function_defs=functions,
            )
            return response
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

    async def create_item(self, validated_response: ValidatedResponse):
        """This is just a temporary that doesnt have a database model"""

        await self.db_client.connect()

        cg = await CodeGraphDBModel.prisma().create(
            data={
                "function_name": validated_response.response.function_name,
                "api_route": validated_response.response.api_route,
                "code_graph": validated_response.response.code_graph,
                "imports": validated_response.response.imports,
            }
        )

        await self.db_client.disconnect()

        return cg

    async def update_item(self, item: CodeGraph):
        await self.db_client.connect()

        cg = await CodeGraphDBModel.prisma().update(
            where={"id": item.id},
            data={
                "function_name": item.function_name,
                "api_route": item.api_route,
                "code_graph": item.code_graph,
                "imports": item.imports,
            },
        )

        await self.db_client.disconnect()

        return cg

    async def get_item(self, item_id: str):
        await self.db_client.connect()

        cg = await CodeGraphDBModel.prisma().find_unique(where={"id": item_id})

        await self.db_client.disconnect()

        return cg

    async def delete_item(self, item_id: str):
        await self.db_client.connect()

        cg = await CodeGraphDBModel.prisma().delete(where={"id": item_id})

        await self.db_client.disconnect()

    async def list_items(self, item_id: str, page: int, page_size: int):
        await self.db_client.connect()

        cg = await CodeGraphDBModel.prisma().find_many(
            skip=(page - 1) * page_size, take=page_size
        )

        await self.db_client.disconnect()

        return cg
