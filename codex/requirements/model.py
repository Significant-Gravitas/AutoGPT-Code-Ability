from typing import List

from pydantic import BaseModel


class Parameter(BaseModel):
    name: str
    param_type: str
    description: str


class RequestModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]


class ResponseModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]


class DatabaseTable(BaseModel):
    description: str
    definition: str


class DatabaseSchema(BaseModel):
    name: str
    description: str
    tables: List[DatabaseTable]


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
    database_schema: DatabaseSchema


class ApplicationRequirements(BaseModel):
    # Application name
    name: str
    # Context on what the application is
    context: str

    api_routes: List[APIRouteRequirement]
