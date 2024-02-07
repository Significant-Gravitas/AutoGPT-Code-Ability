from prisma import Prisma
from prisma.models import User


async def get_or_create_user_by_discord_id(discord_id: int, db_client: Prisma) -> User:
    await db_client.connect()

    user = await User.prisma().find_first(
        where={
            "discord_id": discord_id,
        }
    )

    if not user:
        user = await User.prisma().create(
            data={
                "discord_id": discord_id,
            }
        )

    await db_client.disconnect()

    return user


async def update_user(user: User, db_client: Prisma) -> User:
    await db_client.connect()

    user = await User.prisma().update(
        where={"id": user.id},
        data=user.dict(),
    )

    await db_client.disconnect()

    return user

async def get_user(user_id: int, db_client: Prisma) -> User:
    await db_client.connect()

    user = await User.prisma().find_unique(where={"id": user_id})

    await db_client.disconnect()

    return user