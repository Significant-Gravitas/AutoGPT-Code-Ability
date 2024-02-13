from typing import Dict, List

from prisma.models import APIRouteSpec
from prisma.models import CodeGraph as CodeGraphDBModel
from pydantic import BaseModel


class FunctionDef(BaseModel):
    name: str
    doc_string: str
    args: str
    return_type: str
    function_template: str


class CodeGraph(BaseModel):
    function_name: str
    api_route_spec: APIRouteSpec
    code_graph: str
    imports: List[str]
    function_defs: Dict[str, FunctionDef]
    functions: Dict[str, FunctionDef] | None = None


class ApplicationGraphs(BaseModel):
    code_graphs: List[CodeGraphDBModel]
