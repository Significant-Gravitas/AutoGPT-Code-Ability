from typing import Dict, List

from pydantic import BaseModel

from codex.developer.model import Package


class CompiledRoute(BaseModel):
    service_code: str
    service_file_name: str
    main_function_name: str
    request_param_str: str
    param_names_str: str
    packages: List[Package] | None = None


class Application(BaseModel):
    name: str
    description: str
    server_code: str
    routes: Dict[str, CompiledRoute]
    packages: List[Package] | None = None
