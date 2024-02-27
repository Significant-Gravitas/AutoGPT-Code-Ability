from typing import Dict, List

from prisma.models import APIRouteSpec
from prisma.models import Function as FunctionDBModel
from pydantic import BaseModel


class Package(BaseModel):
    package_name: str
    version: str | None = None
    specifier: str | None = None


class FunctionDef(BaseModel):
    name: str
    args: str
    return_type: str
    is_implemented: bool
    function_template: str
    function_code: str


class GeneratedFunctionResponse(BaseModel):
    function_id: str | None = None

    function_name: str
    api_route_spec: APIRouteSpec
    template: str

    rawCode: str

    packages: List[Package]
    imports: List[str]
    functionCode: str

    functions: Dict[str, FunctionDef] | None = None


class ApplicationGraphs(BaseModel):
    code_graphs: List[FunctionDBModel]
