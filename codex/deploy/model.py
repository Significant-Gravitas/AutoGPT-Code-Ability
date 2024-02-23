from typing import List

from prisma.models import CompletedApp, Package
from pydantic import BaseModel


class Application(BaseModel):
    name: str
    description: str
    server_code: str
    completed_app: CompletedApp
    packages: List[Package]
