from pydantic import BaseModel


class SettingsRequest(BaseModel):
    zip_file: bool
    github_repo: bool
    hosted: bool


class SettingsResponse(BaseModel):
    id: str
    zipfile: bool
    github_repo: bool
    hosted: bool
