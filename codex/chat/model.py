import typing

import fastapi
import pydantic


class ChatRequest(pydantic.BaseModel):
    message: str
    files: typing.List[fastapi.UploadFile]


class ChatResponse(pydantic.BaseModel):
    message: str
