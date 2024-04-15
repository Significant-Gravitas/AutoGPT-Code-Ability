from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


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
    finished_text: Optional[Tuple[str, str]] = None


class Interview(InterviewDBBase):
    id: str
    createdAt: datetime


class NextStepResponse(BaseModel):
    memory: list[InterviewMessageWithResponse]
    questions_to_ask: list[InterviewMessageOptionalId]
    finished: bool = False
    finished_text: Optional[Tuple[str, str]] = None
