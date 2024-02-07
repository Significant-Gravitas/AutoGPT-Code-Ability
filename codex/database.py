from prisma import Prisma
from prisma.models import User

from codex.api_model import Pagination, UserResponse, UsersListResponse


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


async def list_users(page: int, page_size: int, db_client: Prisma) -> UsersListResponse:
    await db_client.connect()

    # Calculate the number of items to skip
    skip = (page - 1) * page_size

    # Query the database for the total number of users
    total_items = await User.count()

    # Query the database for users with pagination
    users = await User.find_many(skip=skip, take=page_size)

    # Calculate the total number of pages
    total_pages = (total_items + page_size - 1) // page_size

    # Create the pagination object
    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    await db_client.disconnect()

    user_responses = [
        UserResponse(
            id=user.id,
            discord_id=user.discord_id,
            createdAt=user.createdAt,
            email=user.email,
            name=user.name,
            role=user.role,
        )
        for user in users
    ]

    # Return both the users and the pagination info
    return UsersListResponse(users=user_responses, pagination=pagination)
