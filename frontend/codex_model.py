import enum
import logging
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Role(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Identifiers(BaseModel):
    user_id: str
    cloud_services_id: str
    app_id: str
    interview_id: str | None = None
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
    cloud_services_id: str = Field(
        ..., description="The unique identifier of the user in cloud services"
    )
    discord_id: Optional[str] = Field(
        None, description="The unique Discord ID of the user"
    )


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    id: str = Field(..., description="The unique identifier of the user")
    role: Role = Field(default=Role.USER, description="The role of the user")


class UserResponse(BaseModel):
    id: str
    cloud_services_id: str
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
    """ApplicationCreate is the model for creating a new application. It includes the name and description of the application (from the base)"""

    description: str = Field(..., description="The description of the application")
    pass


class ApplicationResponse(ApplicationBase):
    id: str = Field(..., description="The unique identifier of the application")
    createdAt: datetime = Field(
        description="The date and time the application was created"
    )
    updatedAt: datetime = Field(
        description="The date and time the application was last updated"
    )
    userid: str


class ApplicationsListResponse(BaseModel):
    applications: List[ApplicationResponse]
    pagination: Optional[Pagination] = None


####### INTERVIEWS #######


class InterviewNextRequest(BaseModel):
    msg: str


class Feature(BaseModel):
    name: str
    functionality: str


class InterviewResponse(BaseModel):
    id: str
    say_to_user: str
    phase: str
    phase_completed: bool


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


class SpecificationBase(BaseModel):
    pass


class SpecificationDelayedResponse(BaseModel):
    message: str


class SpecificationResponse(BaseModel):
    id: str
    createdAt: datetime
    name: str
    context: str
    apiRouteSpecs: List[APIRouteSpecModel] = []


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


class DeploymentResponse(BaseModel):
    id: str
    created_at: datetime
    repo: str


class DeploymentsListResponse(BaseModel):
    deployments: List[DeploymentResponse]
    pagination: Optional[Pagination] = None
