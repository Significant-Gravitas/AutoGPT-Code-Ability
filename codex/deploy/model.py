from typing import List

from prisma.models import CompletedApp, Package
from pydantic import BaseModel, model_validator, ValidationError


class Application(BaseModel):
    name: str
    description: str
    server_code: str
    completed_app: CompletedApp
    packages: List[Package]


class Settings(BaseModel):
    zipfile: bool
    githubRepo: bool
    hosted: bool

    @model_validator(mode="after")
    def check_settings(self):
        zipfile = self.zipfile
        githubRepo = self.githubRepo
        hosted = self.hosted

        if zipfile:
            if githubRepo or hosted:
                raise ValidationError("Cannot have cloud deliverables with zip files")
        elif githubRepo:
            if zipfile:
                raise ValidationError("Cannot have a zip file with github deliverables")

        return self
