from prisma.enums import Role
from prisma.models import Application, User
from prisma.types import UserCreateWithoutRelationsInput

from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    Pagination,
    UserResponse,
    UsersListResponse,
)
from codex.common import test_const


async def create_test_data():
    # user_id_1 = test_const.user_id_1
    # user_id_2 = test_const.user_id_2
    user_1 = test_const.identifier_1
    user_1_discord = test_const.discord_id_1
    user_2 = test_const.identifier_2
    user_2_discord = test_const.discord_id_2
    if not user_1.user_id or not user_2.user_id:
        raise ValueError("User ID not found for user 1 and user 2")
    if not user_1.cloud_services_id or not user_2.cloud_services_id:
        raise ValueError("Cloud Services ID not found for user 1 and user 2")

    await User.prisma().create_many(
        [
            UserCreateWithoutRelationsInput(
                id=user_1.user_id,
                cloudServicesId=user_1.cloud_services_id,
                discordId=user_1_discord,
                role=Role.ADMIN,
                deleted=False,
            ),
            UserCreateWithoutRelationsInput(
                id=user_2.user_id,
                cloudServicesId=user_2.cloud_services_id,
                discordId=user_2_discord,
                role=Role.USER,
                deleted=False,
            ),
            UserCreateWithoutRelationsInput(
                id=test_const.user_id_3,
                cloudServicesId=test_const.cloud_services_id_3,
                discordId=test_const.discord_id_3,
                role=Role.USER,
                deleted=False,
            ),
        ]
    )


async def get_or_create_user_by_cloud_services_id_and_discord_id(
    cloud_services_id: str,
    discord_id: str,
) -> User:
    user = await User.prisma().upsert(
        where={"discordId": discord_id},
        data={
            "create": {
                "discordId": discord_id,
                "cloudServicesId": cloud_services_id,
            },
            "update": {},
        },
    )

    return user


async def get_user(user_id: str) -> User:
    user = await User.prisma().find_unique_or_raise(where={"id": user_id})

    return user


async def list_users(page: int, page_size: int) -> UsersListResponse:
    # Calculate the number of items to skip
    skip = (page - 1) * page_size

    # Query the database for the total number of users
    total_items = await User.prisma().count()
    if total_items == 0:
        return UsersListResponse(
            users=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )

    # Query the database for users with pagination
    users = await User.prisma().find_many(skip=skip, take=page_size)

    # Calculate the total number of pages
    total_pages = (total_items + page_size - 1) // page_size

    # Create the pagination object
    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    user_responses = [
        UserResponse(
            id=user.id,
            cloud_services_id=user.cloudServicesId,
            discord_id=user.discordId,
            createdAt=user.createdAt,
            role=user.role,
        )
        for user in users
    ]

    # Return both the users and the pagination info
    return UsersListResponse(users=user_responses, pagination=pagination)


async def get_app_by_id(user_id: str, app_id: str) -> ApplicationResponse:
    app = await Application.prisma().find_first_or_raise(
        where={
            "id": app_id,
            "userId": user_id,
            "deleted": False,
        },
        include={"User": True},
    )

    return app


async def get_app_response_by_id(user_id: str, app_id: str) -> ApplicationResponse:
    app = await Application.prisma().find_first_or_raise(
        where={
            "id": app_id,
            "userId": user_id,
            "deleted": False,
        },
        include={"User": True},
    )
    if not app.userId:
        raise AssertionError("Application not found")

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
        cloud_services_id=app.User.cloudServicesId if app.User else "",
        description=app.description,
    )


async def create_app(user_id: str, app_data: ApplicationCreate) -> ApplicationResponse:
    app = await Application.prisma().create(
        data={
            "name": app_data.name,
            "description": app_data.description,
            "userId": user_id,
        },
        include={"User": True},
    )

    if not app.userId:
        raise AssertionError("Application not found")

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
        cloud_services_id=app.User.cloudServicesId if app.User else "",
    )


async def delete_app(user_id: str, app_id: str) -> None:
    await Application.prisma().update(
        where={
            "id": app_id,
            "userId": user_id,
        },
        data={"deleted": True},
    )


async def list_apps(
    user_id: str, page: int, page_size: int
) -> ApplicationsListResponse:
    skip = (page - 1) * page_size
    total_items = await Application.prisma().count(
        where={"userId": user_id, "deleted": False}
    )
    apps = await Application.prisma().find_many(
        where={"userId": user_id, "deleted": False},
        include={"User": True},
        skip=skip,
        take=page_size,
    )
    if apps:
        total_pages = (total_items + page_size - 1) // page_size

        applications_response = [
            ApplicationResponse(
                id=app.id,
                createdAt=app.createdAt,
                updatedAt=app.updatedAt,
                name=app.name,
                userid=app.userId if app.userId else "",
                cloud_services_id=app.User.cloudServicesId if app.User else "",
            )
            for app in apps
        ]

        pagination = Pagination(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )

        return ApplicationsListResponse(
            applications=applications_response, pagination=pagination
        )
    else:
        return ApplicationsListResponse(
            applications=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )
