from langchain.pydantic_v1 import BaseModel
from typing import Dict, List
import ast
import logging
from typing import Dict, List

import ast
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class CodeGraph(BaseModel):
    name: str
    code_graph: str
    imports: List[str]
    functions: Dict[str, str]

code_model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-0125-preview",
    max_tokens=4095,
)
    
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
            arg_name = arg.arg
            arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Unknown'
            args.append(f"{arg_name}: {arg_type}")
        args_str = ', '.join(args)
        return_type = ast.unparse(node.returns) if node.returns else 'None'
        print(f"Function '{node.name}' definition ({args_str}) -> {return_type}:")
        self.functions[node.name] = ast.unparse(node)
        self.generic_visit(node)

