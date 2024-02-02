from typing import Dict, List

from langchain.pydantic_v1 import BaseModel
from codex.developer import Package


class CompiledRoute(BaseModel):
    description: str
    service_code: str
    service_file_name: str
    packages: List[Package] | None = None
    
class Application(BaseModel):
    name: str
    description: str
    server_code: str
    routes: Dict[str, CompiledRoute]
    packages: List[Package] | None = None