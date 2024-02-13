from typing import List

from langchain.pydantic_v1 import BaseModel


class Package(BaseModel):
    package_name: str
    version: str | None = None
    specifier: str | None = None


class Function(BaseModel):
    name: str
    doc_string: str
    args: str
    return_type: str
    code: str
    packages: List[Package] | None = None


class CheckComplexity(BaseModel):
    is_complex: bool


class GeneratedCode(BaseModel):
    packages: List[Package]
    code: Function
