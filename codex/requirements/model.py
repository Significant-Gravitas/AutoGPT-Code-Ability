from typing import List

from pydantic import BaseModel


class Parameter(BaseModel):
    name: str
    param_type: str
    description: str

    def __str__(self):
        return f"- **Name**: {self.name}\n  - **Type**: {self.param_type}\n  - **Description**: {self.description}\n"


class RequestModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

    def __str__(self):
        params_str = "\n".join(str(param) for param in self.params)
        return f"### {self.name}\n**Description**: {self.description}\n**Parameters**:\n{params_str}\n"


class ResponseModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

    def __str__(self):
        params_str = "\n".join(str(param) for param in self.params)
        return f"### {self.name}\n**Description**: {self.description}\n**Parameters**:\n{params_str}\n"


class DatabaseTable(BaseModel):
    description: str
    definition: str

    def __str__(self):
        return f"**Description**: {self.description}\n**Definition**:\n```\n{self.definition}\n```\n"


class DatabaseSchema(BaseModel):
    name: str
    description: str
    tables: List[DatabaseTable]

    def __str__(self):
        tables_str = "\n".join(str(table) for table in self.tables)
        return f"## {self.name}\n**Description**: {self.description}\n**Tables**:\n{tables_str}\n"


class APIRouteRequirement(BaseModel):
    # I'll use these to generate the endpoint
    method: str
    path: str

    # This is context on what this api route should do
    description: str

    # This is the model for the request and response
    request_model: RequestModel
    response_model: ResponseModel

    # This is the database schema this api route will use
    # I'm thinking it will be a prisma table schema or maybe a list of table schemas
    # See the schema.prisma file in the codex directory more info
    database_schema: DatabaseSchema | None = None

    def __str__(self):
        db_schema_str = (
            f"**Database Schema**:\n{str(self.database_schema)}\n"
            if self.database_schema
            else ""
        )
        return (
            f"**Method**: `{self.method}`\n"
            f"**Path**: `{self.path}`\n"
            f"**Description**: {self.description}\n"
            f"**Request Model**:\n{str(self.request_model)}\n"
            f"**Response Model**:\n{str(self.response_model)}\n"
            f"{db_schema_str}"
        )


class ApplicationRequirements(BaseModel):
    # Application name
    name: str
    # Context on what the application is
    context: str

    api_routes: List[APIRouteRequirement]

    def __str__(self):
        api_routes_str = "\n".join(str(route) for route in self.api_routes)
        return f"# {self.name}\n**Context**: {self.context}\n**API Routes**:\n{api_routes_str}\n"
