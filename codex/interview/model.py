import enum

from pydantic import BaseModel


class AppFeature(BaseModel):
    reasoning: str
    name: str
    functionality: str


class UndestandRequest(BaseModel):
    thoughts: str
    features: list[AppFeature] | None = None
    say_to_user: str
    phase_completed: bool


class Action(str, enum.Enum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"


class AppFeatureUpdate(BaseModel):
    action: Action
    id: int
    reasoning: str | None = None
    name: str | None = None
    functionality: str | None = None


class UpdateUnderstanding(BaseModel):
    thoughts: str
    features: list[AppFeatureUpdate] | None = None
    say_to_user: str
    phase_completed: bool


class Feature(BaseModel):
    name: str
    functionality: str


class InterviewResponse(BaseModel):
    id: str
    say_to_user: str
    phase: str
    phase_completed: bool


class Module(BaseModel):
    """
    A Software Module for the application
    """

    action: Action
    id: int
    name: str | None = None
    functionality: str | None = None
    interaction_with_other_modules: list[str] | None = None


class ModuleResponse(BaseModel):
    """
    This is the response model for the ModuleGenerationBlock
    """

    thoughts: str
    say_to_user: str
    modules: list[Module] | None = None
    access_roles: list[str]
    phase_completed: bool
