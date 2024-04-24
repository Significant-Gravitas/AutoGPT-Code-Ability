import logging

from fastapi import APIRouter, Response

from prisma.models import Settings

from codex.settings.model import SettingsResponse, SettingsRequest

logger = logging.getLogger(__name__)

settings_router = APIRouter(
    tags=["settings"],
)


@settings_router.post("/user/{user_id}/settings/", response_model=SettingsResponse)
async def configure_settings(
    user_id, settings: SettingsRequest
) -> Response | SettingsResponse:
    updated_settings = await Settings.prisma().upsert(
        where={
            "user_id": user_id,
        },
        data={
            "create": {
                "zipFile": settings.zip_file,
                "gitHubRepo": settings.github_repo,
                "hosted": settings.hosted,
                "userId": user_id,
            },
            "update": {
                "zipFile": settings.zip_file,
                "gitHubRepo": settings.github_repo,
                "hosted": settings.hosted,
            },
        },
    )

    return SettingsResponse(
        id=updated_settings.id,
        zip_file=updated_settings.zipFile,
        github_repo=updated_settings.githubRepo,
        hosted=updated_settings.hosted,
    )


@settings_router.get("/user/{user_id}/settings/", response_model=SettingsResponse)
async def get_settings(
    user_id,
) -> Response | SettingsResponse:
    settings = await Settings.prisma().find(
        where={
            "user_id": user_id,
        }
    )

    return SettingsResponse(
        id=settings.id,
        zip_file=settings.zipFile,
        github_repo=settings.gitHubRepo,
        hosted=settings.hosted,
    )
