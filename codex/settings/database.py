from prisma.models import Settings


async def get_settings(user_id: str) -> Settings:
    settings = await Settings.prisma().find_unique_or_raise(
        where={"user_id": user_id, "deleted": False},
    )

    return settings
