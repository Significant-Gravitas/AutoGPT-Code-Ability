from typing import List

from langchain.pydantic_v1 import BaseModel


class Package(BaseModel):
    packageName: str
    version: str
    specifier: str


class Function(BaseModel):
    name: str
    doc_string: str
    args: str
    return_type: str
    code: str
    packages: List[Package] | None = None
