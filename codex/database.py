from datetime import datetime

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
    user_id_1 = test_const.user_id_1
    user_id_2 = test_const.user_id_2

    await User.prisma().create_many(
        [
            UserCreateWithoutRelationsInput(
                id=user_id_1,
                cloudServicesId="123456789",
                discordId="123456788",
                role=Role.ADMIN,
                deleted=False,
            ),
            UserCreateWithoutRelationsInput(
                id=user_id_2,
                cloudServicesId="234567890",
                discordId="234567891",
                role=Role.USER,
                deleted=False,
            ),
        ]
    )

    # Insert applications
    await Application.prisma().create_many(
        [
            {
                "name": "Availability Checker",
                "deleted": False,
                "id": test_const.app_id_1,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Invoice Generator",
                "deleted": False,
                "id": test_const.app_id_2,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Appointment Optimization Tool",
                "deleted": False,
                "id": test_const.app_id_3,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Distance Calculator",
                "deleted": False,
                "id": test_const.app_id_4,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Profile Management System",
                "deleted": False,
                "id": test_const.app_id_5,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Calendar Booking System",
                "deleted": False,
                "id": test_const.app_id_6,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Inventory Management System",
                "deleted": False,
                "id": test_const.app_id_7,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Invoice Payment Tracking",
                "deleted": False,
                "id": test_const.app_id_8,
                "userId": user_id_1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Survey Tool",
                "deleted": False,
                "id": test_const.app_id_9,
                "userId": user_id_2,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Scurvey Tool",
                "deleted": True,
                "id": test_const.app_id_10,
                "userId": user_id_2,
                "updatedAt": datetime.now(),
            },
            {
                "name": "TicTacToe Game",
                "deleted": False,
                "id": test_const.app_id_9,
                "userId": user_id_2,
                "updatedAt": datetime.now(),
            }
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
        }
    )
    assert app.userId, "Application not found"

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
    )


async def create_app(user_id: str, app_data: ApplicationCreate) -> ApplicationResponse:
    app = await Application.prisma().create(
        data={
            "name": app_data.name,
            "userId": user_id,
        }
    )

    assert app.userId, "Application not found"

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
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
        where={"userId": user_id, "deleted": False}, skip=skip, take=page_size
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
