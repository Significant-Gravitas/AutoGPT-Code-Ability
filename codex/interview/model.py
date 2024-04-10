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


class InterviewResponse(BaseModel):
    id: str
    say_to_user: str
    features: list[str] | None = None
    phase_completed: bool
