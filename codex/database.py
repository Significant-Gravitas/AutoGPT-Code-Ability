from prisma import Prisma
from prisma.models import User, Application

from codex.api_model import Pagination, UserResponse, UsersListResponse, ApplicationCreate, ApplicationResponse, ApplicationsListResponse


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


async def get_app_by_id(user_id: int, app_id: int, db_client: Prisma) -> ApplicationResponse:
    await db_client.connect()

    app = await Application.prisma().find_first(
        where={
            "id": app_id,
            "userid": user_id,
        }
    )

    await db_client.disconnect()

    if app:
        return ApplicationResponse(
            id=app.id,
            createdAt=app.createdAt,
            updatedAt=app.updatedAt,
            name=app.name,
            userid=app.userid,
        )
    else:
        return None


async def create_app(user_id: int, app_data: ApplicationCreate, db_client: Prisma) -> ApplicationResponse:
    await db_client.connect()

    app = await Application.prisma().create(
        data={
            "name": app_data.name,
            "userid": user_id,
        }
    )

    await db_client.disconnect()

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userid,
    )


async def delete_app(user_id: int, app_id: int, db_client: Prisma) -> None:
    await db_client.connect()

    await Application.prisma().delete_many(
        where={
            "id": app_id,
            "userid": user_id,
        }
    )

    await db_client.disconnect()


async def list_apps(user_id: int, page: int, page_size: int, db_client: Prisma) -> ApplicationsListResponse:
    await db_client.connect()

    skip = (page - 1) * page_size
    total_items = await Application.count(
        where={"userid": user_id}
    )
    apps = await Application.prisma().find_many(
        where={"userid": user_id},
        skip=skip,
        take=page_size
    )

    total_pages = (total_items + page_size - 1) // page_size

    await db_client.disconnect()

    applications_response = [
        ApplicationResponse(
            id=app.id,
            createdAt=app.createdAt,
            updatedAt=app.updatedAt,
            name=app.name,
            userid=app.userid,
        ) for app in apps
    ]

    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    return ApplicationsListResponse(applications=applications_response, pagination=pagination)