from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


class AppFeature(BaseModel):
    reasoning: str
    name: str
    functionality: str


class UndestandRequest(BaseModel):
    thoughts: str
    features: list[AppFeature] | None = None
    say_to_user: str
    phase_completed: str


class AppCheckList(BaseModel):
    notifications: bool
    database: bool
    caching: bool

    gdpr_compliance: bool
    stripe_integration: bool
    analytics: bool

    email_integration: bool
    social_media_integration: bool
    search_functionality: bool
    api_integration: bool
    apis_required: list[str]

    security_audit: bool
    backup_and_recovery: bool


class InterviewMessage(BaseModel):
    model_config = ConfigDict(strict=False)

    id: str
    tool: str
    content: str


class InterviewMessageWithResponse(InterviewMessage):
    response: str


class InterviewMessageOptionalId(BaseModel):
    model_config = ConfigDict(strict=False)

    id: Optional[str] = Field(None)
    tool: str
    content: str


class InterviewMessageWithResponseOptionalId(InterviewMessageOptionalId):
    response: str


class InterviewMessageUse(BaseModel):
    model_config = ConfigDict(strict=False)

    uses: List[InterviewMessageOptionalId | InterviewMessageWithResponseOptionalId]


class InterviewDBBase(BaseModel):
    app_name: str
    project_description: str
    questions: List[InterviewMessageOptionalId | InterviewMessageWithResponseOptionalId]
    finished: bool = False


class Interview(InterviewDBBase):
    id: str
    createdAt: datetime


class NextStepResponse(BaseModel):
    memory: list[InterviewMessageWithResponse]
    questions_to_ask: list[InterviewMessageOptionalId]
    finished: bool = False
    finished_text: Optional[Tuple[str, str]] = None
