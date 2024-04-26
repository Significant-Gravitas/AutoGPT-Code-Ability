from typing import List, Optional

from pydantic import BaseModel, model_validator, ValidationError
from prisma.models import CompiledRoute, CompletedApp, Package


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


class Settings(BaseModel):
    zipfile: bool
    githubRepo: bool
    hosted: bool

    @model_validator(mode="after")
    def check_settings(self):
        zipfile = self.zipfile
        githubRepo = self.githubRepo
        hosted = self.hosted

        if not (self.zipfile or self.githubRepo):
            raise ValidationError("At least one deployment method must be selected")

        if zipfile:
            if githubRepo or hosted:
                raise ValidationError("Cannot have cloud deliverables with zip files")
        elif githubRepo:
            if zipfile:
                raise ValidationError("Cannot have a zip file with github deliverables")

        return self
