from typing import Dict, List

from prisma.models import CompiledRoute as CompiledRouteDBModel
from prisma.models import CompletedApp
from pydantic import BaseModel

from codex.develop.model import Package


class CompiledRoute(BaseModel):
    method: str
    service_code: str
    service_file_name: str
    main_function_name: str
    request_param_str: str
    param_names_str: str
    return_type: str
    packages: List[Package] | None = None
    compiled_route: CompiledRouteDBModel | None = None


class Application(BaseModel):
    name: str
    description: str
    server_code: str
    completed_app: CompletedApp | None = None
    routes: Dict[str, CompiledRoute]
    packages: List[Package] | None = None
