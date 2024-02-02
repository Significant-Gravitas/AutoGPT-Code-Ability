from typing import Dict, List

from langchain.pydantic_v1 import BaseModel


class FunctionDef(BaseModel):
    name: str
    doc_string: str
    args: str
    return_type: str
    function_template: str


class CodeGraph(BaseModel):
    function_name: str
    api_route: str
    code_graph: str
    imports: List[str]
    function_defs: Dict[str, FunctionDef]
    functions: Dict[str, FunctionDef] | None = None
