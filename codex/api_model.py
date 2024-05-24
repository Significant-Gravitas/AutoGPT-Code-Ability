import logging
from datetime import datetime
from typing import List, Optional

import prisma
from prisma.enums import AccessLevel, Role
from prisma.models import ObjectField, ObjectType, Specification
from pydantic import BaseModel, Field

from codex.common.parse_prisma import parse_prisma_schema

logger = logging.getLogger(__name__)


class Identifiers(BaseModel):
    user_id: str | None = None
    cloud_services_id: str | None = None
    app_id: str | None = None
    interview_id: str | None = None
    spec_id: str | None = None
    compiled_route_id: str | None = None
    function_id: str | None = None
    completed_app_id: str | None = None
    deployment_id: str | None = None


class Pagination(BaseModel):
    total_items: int = Field(..., description="Total number of items.", examples=[42])
    total_pages: int = Field(..., description="Total number of pages.", examples=[97])
    current_page: int = Field(
        ..., description="Current_page page number.", examples=[1]
    )
    page_size: int = Field(..., description="Number of items per page.", examples=[25])


###### USERS ######


class UserBase(BaseModel):
    discord_id: Optional[str] = Field(
        None, description="The unique Discord ID of the user"
    )
    cloud_services_id: str = Field(
        ..., description="The unique identifier of the user in cloud services"
    )


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    id: str = Field(..., description="The unique identifier of the user")

    role: Optional[Role] = Field(None, description="The new role of the user")


class UserResponse(BaseModel):
    id: str
    discord_id: str
    cloud_services_id: str
    createdAt: datetime
    role: Role


class UsersListResponse(BaseModel):
    users: List[UserResponse]
    pagination: Optional[Pagination] = None


####### APPS #######
class FunctionRequest(BaseModel):
    """
    A request to generate a correctly formated function spec
    """

    name: str
    description: str
    inputs: str
    outputs: str


class ApplicationBase(BaseModel):
    name: str = Field(..., description="The name of the application")
    description: Optional[str] = Field(
        None, description="A description of the application"
    )


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(BaseModel):
    id: str
    createdAt: datetime
    updatedAt: datetime
    name: str
    userid: str
    cloud_services_id: str
    description: str | None = None


class ApplicationsListResponse(BaseModel):
    applications: List[ApplicationResponse]
    pagination: Optional[Pagination] = None


###### SPECS ######
class InterviewNextRequest(BaseModel):
    msg: str


class ParamModel(BaseModel):
    id: str
    createdAt: datetime
    name: str
    description: str
    param_type: str


class RequestObjectModel(BaseModel):
    id: str
    createdAt: datetime
    name: str
    description: str
    params: List[ParamModel] = []


class ResponseObjectModel(BaseModel):
    id: str
    createdAt: datetime
    name: str
    description: str
    params: List[ParamModel] = []


class APIRouteSpecModel(BaseModel):
    id: str
    createdAt: datetime
    method: str
    path: str
    description: str
    requestObject: Optional[RequestObjectModel] = None
    responseObject: Optional[ResponseObjectModel] = None


class SpecificationCreate(BaseModel):
    description: str


class SpecificationUpdate(prisma.models.Specification, BaseModel):
    apiRouteSpecs: List[APIRouteSpecModel] = []


class InputParamModel(BaseModel):
    name: str
    description: str
    param_type: str


class InputRequestResponseModel(BaseModel):
    name: str
    description: str
    params: List[InputParamModel] = []


class SpecificationAddRouteToModule(BaseModel):
    function_name: str
    access_level: AccessLevel
    allowed_access_roles: List[str]
    method: str
    path: str
    description: str
    requestObject: Optional["ObjectTypeModel"] = None
    responseObject: Optional["ObjectTypeModel"] = None


class DatabaseEnums(BaseModel):
    name: str
    description: str
    values: list[str]
    definition: str

    def __str__(self):
        return f"**Enum: {self.name}**\n\n**Values**:\n{', '.join(self.values)}\n"


class DatabaseTable(BaseModel):
    name: str | None = None
    description: str
    definition: str  # prisma model for a table

    def __str__(self):
        return f"**Table: {self.name}**\n\n\n\n**Definition**:\n```\n{self.definition}\n```\n"


class DatabaseSchema(BaseModel):
    name: str  # name of the database schema
    description: str  # context on what the database schema is
    tables: List[DatabaseTable]  # list of tables in the database schema
    enums: List[DatabaseEnums]

    def __str__(self):
        tables_str = "\n".join(str(table) for table in self.tables)
        enum_str = "\n".join(str(enum) for enum in self.enums)
        return f"## {self.name}\n**Description**: {self.description}\n**Tables**:\n{tables_str}\n**Enums**:\n{enum_str}\n"


class ModuleWrapper(BaseModel):
    id: str
    name: str
    description: str
    interactions: str
    apiRouteSpecs: List[APIRouteSpecModel] = []


class SpecificationResponse(BaseModel):
    id: str
    createdAt: datetime
    name: str
    context: str
    modules: List[ModuleWrapper] = []
    databaseSchema: Optional[DatabaseSchema] = None

    @staticmethod
    def from_specification(specification: Specification) -> "SpecificationResponse":
        logger.debug(specification.model_dump_json())
        module_out = []
        modules: list[prisma.models.Module] | None = (
            specification.Modules if specification.Modules else None
        )
        if modules is None:
            raise ValueError("No routes found for the specification")
        for module in modules:
            if module.ApiRouteSpecs:
                routes = []
                for route in module.ApiRouteSpecs:
                    routes.append(
                        APIRouteSpecModel(
                            id=route.id,
                            createdAt=route.createdAt,
                            method=str(route.method),
                            path=route.path,
                            description=route.description,
                            requestObject=RequestObjectModel(
                                id=route.RequestObject.id,
                                createdAt=route.RequestObject.createdAt,
                                name=route.RequestObject.name,
                                description=route.RequestObject.description or "",
                                params=[
                                    ParamModel(
                                        id=param.id,
                                        createdAt=param.createdAt,
                                        name=param.name,
                                        description=param.description or "",
                                        param_type=param.typeName,
                                    )
                                    for param in route.RequestObject.Fields or []
                                ],
                            )
                            if route.RequestObject
                            else None,
                            responseObject=ResponseObjectModel(
                                id=route.ResponseObject.id,
                                createdAt=route.ResponseObject.createdAt,
                                name=route.ResponseObject.name,
                                description=route.ResponseObject.description or "",
                                params=[
                                    ParamModel(
                                        id=param.id,
                                        createdAt=param.createdAt,
                                        name=param.name,
                                        description=param.description or "",
                                        param_type=param.typeName,
                                    )
                                    for param in route.ResponseObject.Fields or []
                                ],
                            )
                            if route.ResponseObject
                            else None,
                        )
                    )
                module_out.append(
                    ModuleWrapper(
                        id=module.id,
                        apiRouteSpecs=routes,
                        name=module.name,
                        description=module.description,
                        interactions=module.interactions,
                    )
                )
            else:
                module_out.append(
                    ModuleWrapper(
                        id=module.id,
                        name=module.name,
                        description=module.description,
                        interactions=module.interactions,
                    )
                )
        db_schema = None
        if specification.DatabaseSchema:

            def convert_to_table(table: prisma.models.DatabaseTable) -> DatabaseTable:
                return DatabaseTable(
                    name=table.name or "ERROR: Unknown Table Name",
                    description=table.description,
                    definition=table.definition,
                )

            def convert_to_enum(table: prisma.models.DatabaseTable) -> DatabaseEnums:
                return DatabaseEnums(
                    name=table.name or "ERROR: Unknown ENUM Name",
                    description=table.description,
                    values=parse_prisma_schema(table.definition)
                    .enums[table.name or "ERROR: Unknown ENUM Name"]
                    .values,
                    definition=table.definition,
                )

            db_schema = DatabaseSchema(
                name=specification.DatabaseSchema.name or "Database Schema",
                tables=[
                    convert_to_table(table)
                    for table in specification.DatabaseSchema.DatabaseTables or []
                    if not table.isEnum
                ],
                enums=[
                    convert_to_enum(table)
                    for table in specification.DatabaseSchema.DatabaseTables or []
                    if table.isEnum
                ],
                description=specification.DatabaseSchema.description,
            )
        ret_obj = SpecificationResponse(
            id=specification.id,
            createdAt=specification.createdAt,
            name="",
            context="",
            modules=module_out,
            databaseSchema=db_schema,
        )

        return ret_obj


class SpecificationsListResponse(BaseModel):
    specs: List[SpecificationResponse] | List[None] = []
    pagination: Optional[Pagination] = None


### Deliverables ###


class CompiledRouteModel(BaseModel):
    id: str
    createdAt: datetime
    description: str
    code: str


class DeliverableResponse(BaseModel):
    id: str
    created_at: datetime
    name: str
    description: str


class DeliverablesListResponse(BaseModel):
    deliverables: List[DeliverableResponse]
    pagination: Optional[Pagination] = None


### Deployements ###


class DeploymentMetadata(BaseModel):
    id: str
    created_at: datetime
    repo: str


class DeploymentRequest(BaseModel):
    zip_file: bool
    github_repo: bool
    hosted: bool


class DeploymentResponse(DeploymentMetadata):
    pass


class DeploymentsListResponse(BaseModel):
    deployments: List[DeploymentMetadata]
    pagination: Optional[Pagination] = None


class ObjectTypeModel(BaseModel):
    name: str = Field(description="The name of the object")
    code: Optional[str] = Field(description="The code of the object", default=None)
    description: Optional[str] = Field(
        description="The description of the object", default=None
    )
    Fields: List["ObjectFieldModel"] = Field(description="The fields of the object")
    is_pydantic: bool = Field(
        description="Whether the object is a pydantic model", default=True
    )
    is_implemented: bool = Field(
        description="Whether the object is implemented", default=True
    )
    is_enum: bool = Field(description="Whether the object is an enum", default=False)

    def __init__(self, db_obj: ObjectType | None = None, **data):
        if not db_obj:
            super().__init__(**data)
            return

        super().__init__(
            name=db_obj.name,
            code=db_obj.code,
            description=db_obj.description,
            is_pydantic=db_obj.isPydantic,
            is_enum=db_obj.isEnum,
            Fields=[ObjectFieldModel(db_obj=f) for f in db_obj.Fields or []],
            **data,
        )


class ObjectFieldModel(BaseModel):
    name: str = Field(description="The name of the field")
    description: Optional[str] = Field(
        description="The description of the field", default=None
    )
    type: str = Field(
        description="The type of the field. Can be a string like List[str] or an use any of they related types like list[User]",
    )
    value: Optional[str] = Field(description="The value of the field", default=None)
    related_types: Optional[List[ObjectTypeModel]] = Field(
        description="The related types of the field", default=[]
    )

    def __init__(self, db_obj: ObjectField | None = None, **data):
        if not db_obj:
            super().__init__(**data)
            return

        super().__init__(
            name=db_obj.name,
            description=db_obj.description,
            type=db_obj.typeName,
            value=db_obj.value,
            related_types=[
                ObjectTypeModel(db_obj=t) for t in db_obj.RelatedTypes or []
            ],
            **data,
        )
