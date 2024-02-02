from typing import Dict, List

from langchain.pydantic_v1 import BaseModel


class Param(BaseModel):
    param_type: str
    name: str

    def __eq__(self, other):
        if not isinstance(other, Param):
            return False

        return self.param_type.lower() == other.param_type.lower()


class FunctionDef(BaseModel):
    name: str
    args: List[Param]
    return_type: str
    template: str


class CodeGraph(BaseModel):
    name: str
    code_graph: str
    imports: List[str]
    function_defs: Dict[str, FunctionDef]
    functions: Dict[str, FunctionDef] | None = None
