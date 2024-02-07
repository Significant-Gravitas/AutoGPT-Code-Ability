from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

###### USERS ######


class Role(str, Enum):
    user = "USER"
    admin = "ADMIN"


class UserBase(BaseModel):
    discord_id: Optional[str] = Field(
        None, description="The unique Discord ID of the user"
    )
    email: Optional[EmailStr] = Field(None, description="The email address of the user")
    name: Optional[str] = Field(None, description="The name of the user")
    role: Role = Field(default=Role.user, description="The role of the user")


class UserCreate(UserBase):
    password: str = Field(..., description="The password of the user")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(
        None, description="The new email address of the user"
    )
    name: Optional[str] = Field(None, description="The new name of the user")
    role: Optional[Role] = Field(None, description="The new role of the user")
    password: Optional[str] = Field(None, description="The new password of the user")


class UserResponse(BaseModel):
    id: int
    discord_id: str
    createdAt: datetime
    email: Optional[EmailStr]
    name: Optional[str]
    role: Role


class UsersListResponse(BaseModel):
    users: List[UserResponse]


####### APPS #######


class ApplicationBase(BaseModel):
    name: str = Field(..., description="The name of the application")


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(BaseModel):
    id: int
    createdAt: datetime
    updatedAt: datetime
    name: str
    userid: int


class ApplicationsListResponse(BaseModel):
    applications: List[ApplicationResponse]


###### SPECS ######


class ParamModel(BaseModel):
    id: int
    createdAt: datetime
    name: str
    description: str
    param_type: str


class RequestObjectModel(BaseModel):
    id: int
    createdAt: datetime
    name: str
    description: str
    params: List[ParamModel] = []


class ResponseObjectModel(BaseModel):
    id: int
    createdAt: datetime
    name: str
    description: str
    params: List[ParamModel] = []


class APIRouteSpecModel(BaseModel):
    id: int
    createdAt: datetime
    method: str
    path: str
    description: str
    requestObject: Optional[RequestObjectModel] = None
    responseObject: Optional[ResponseObjectModel] = None


class SpecificationModel(BaseModel):
    id: int
    createdAt: datetime
    name: str
    context: str
    apiRoutes: List[APIRouteSpecModel] = []


class SpecificationResponse(BaseModel):
    specification: SpecificationModel


class SpecificationsListResponse(BaseModel):
    specifications: List[SpecificationModel]


### Deliverables ###


class CompiledRouteModel(BaseModel):
    id: int
    createdAt: datetime
    description: str
    code: str
    # codeGraphId: Optional[int] = None  # Omitted to simplify, can be included if needed


class CompletedAppModel(BaseModel):
    id: int
    createdAt: datetime
    name: str
    description: str
    compiledRoutes: List[CompiledRouteModel] = []


class DeliverableResponse(BaseModel):
    completedApp: CompletedAppModel


class DeliverablesListResponse(BaseModel):
    completedApps: List[CompletedAppModel]


### Deployements ###


class DeploymentMetadata(BaseModel):
    id: int
    createdAt: datetime
    fileName: str
    fileSize: int
    downloadUrl: str  # Assuming there's a URL to download the zip file


class DeploymentResponse(BaseModel):
    deployment: DeploymentMetadata


class DeploymentsListResponse(BaseModel):
    deployments: List[DeploymentMetadata]
