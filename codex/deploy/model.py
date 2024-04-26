from typing import List, Optional

from prisma.models import CompiledRoute, CompletedApp, Package
from pydantic import BaseModel


class Application(BaseModel):
    name: str
    description: str
    server_code: str
    app_code: str = ""
    completed_app: CompletedApp
    companion_completed_app: Optional[CompletedApp] = None
    packages: List[Package]

    def get_compiled_routes(self) -> List[CompiledRoute]:
        routes = self.completed_app.CompiledRoutes or []
        if self.companion_completed_app:
            routes += self.companion_completed_app.CompiledRoutes or []
        return routes
