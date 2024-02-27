import logging
from datetime import datetime
from typing import List, Optional

from prisma.enums import Role
from prisma.models import Specification
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)


class Identifiers(BaseModel):
    user_id: str
    app_id: str
    spec_id: str | None = None
    completed_app_id: str | None = None
    deployment_id: str | None = None
    function_def_id: str | None = None


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
    email: Optional[EmailStr] = Field(None, description="The email address of the user")
    name: Optional[str] = Field(None, description="The name of the user")
    role: Role = Field(default=Role.USER, description="The role of the user")


class UserCreate(UserBase):
    password: str = Field(..., description="The password of the user")


class UserUpdate(BaseModel):
    id: str = Field(..., description="The unique identifier of the user")
    email: Optional[EmailStr] = Field(
        None, description="The new email address of the user"
    )
    name: Optional[str] = Field(None, description="The new name of the user")
    role: Optional[Role] = Field(None, description="The new role of the user")
    password: Optional[str] = Field(None, description="The new password of the user")


class UserResponse(BaseModel):
    id: str
    discord_id: str
    createdAt: datetime
    role: Role


class UsersListResponse(BaseModel):
    users: List[UserResponse]
    pagination: Optional[Pagination] = None


####### APPS #######


class ApplicationBase(BaseModel):
    name: str = Field(..., description="The name of the application")


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(BaseModel):
    id: str
    createdAt: datetime
    updatedAt: datetime
    name: str
    userid: str


class ApplicationsListResponse(BaseModel):
    applications: List[ApplicationResponse]
    pagination: Optional[Pagination] = None


###### SPECS ######


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


class SpecificationResponse(BaseModel):
    id: str
    createdAt: datetime
    name: str
    context: str
    apiRouteSpecs: List[APIRouteSpecModel] = []

    @staticmethod
    def from_specification(specification: Specification) -> "SpecificationResponse":
        logger.debug(specification.model_dump_json())
        routes = []
        if specification.ApiRouteSpecs is None:
            raise ValueError("No routes found for the specification")
        for route in specification.ApiRouteSpecs:
            if route.RequestObject is None:
                raise ValueError("No request object found for the route")
            if route.ResponseObject is None:
                raise ValueError("No response object found for the route")
            routes.append(
                APIRouteSpecModel(
                    id=route.id,
                    createdAt=route.createdAt,
                    method=route.method,
                    path=route.path,
                    description=route.description,
                    requestObject=RequestObjectModel(
                        id=route.RequestObject.id,
                        createdAt=route.RequestObject.createdAt,
                        name=route.RequestObject.name,
                        description=route.RequestObject.description,
                        params=[
                            ParamModel(
                                id=param.id,
                                createdAt=param.createdAt,
                                name=param.name,
                                description=param.description,
                                param_type=param.typeName,
                            )
                            for param in route.RequestObject.Fields or []
                        ],
                    ),
                    responseObject=ResponseObjectModel(
                        id=route.ResponseObject.id,
                        createdAt=route.ResponseObject.createdAt,
                        name=route.ResponseObject.name,
                        description=route.ResponseObject.description,
                        params=[
                            ParamModel(
                                id=param.id,
                                createdAt=param.createdAt,
                                name=param.name,
                                description=param.description,
                                param_type=param.typeName,
                            )
                            for param in route.ResponseObject.Fields or []
                        ],
                    ),
                )
            )

        ret_obj = SpecificationResponse(
            id=specification.id,
            createdAt=specification.createdAt,
            name=specification.name,
            context=specification.context,
            apiRouteSpecs=routes,
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
    file_name: str
    file_size: int


class DeploymentResponse(DeploymentMetadata):
    pass


class DeploymentsListResponse(BaseModel):
    deployments: List[DeploymentMetadata]
    pagination: Optional[Pagination] = None
