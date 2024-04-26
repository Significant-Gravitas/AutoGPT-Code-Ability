from pydantic import BaseModel


class AppFeature(BaseModel):
    reasoning: str
    name: str
    functionality: str


class UnderstandRequest(BaseModel):
    thoughts: str
    features: list[AppFeature] | None = None
    say_to_user: str
    phase_completed: bool


class Feature(BaseModel):
    name: str
    functionality: str


class InterviewResponse(BaseModel):
    id: str
    say_to_user: str
    features: list[Feature] | None = None
    phase_completed: bool
