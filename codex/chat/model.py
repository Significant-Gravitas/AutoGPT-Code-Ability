import pydantic


class ChatRequest(pydantic.BaseModel):
    message: str


class ChatResponse(pydantic.BaseModel):
    id: str
    message: str
