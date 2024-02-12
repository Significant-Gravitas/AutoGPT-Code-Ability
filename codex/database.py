from datetime import datetime

from prisma.models import Application, CodexUser, Deployment

from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    DeliverableResponse,
    DeploymentMetadata,
    DeploymentResponse,
    DeploymentsListResponse,
    Pagination,
    UserResponse,
    UsersListResponse,
)


async def create_test_data():
    await CodexUser.prisma().create_many(
        [
            {
                "discord_id": "123456789",
                "email": "joe.blogs@example.com",
                "name": "Joe Blogs",
                "role": "ADMIN",
                "password": "password123",
                "deleted": False,
            },
            {
                "discord_id": "234567890",
                "email": "jane.doe@example.com",
                "name": "Jane Doe",
                "role": "USER",
                "password": "password123",
                "deleted": False,
            },
        ]
    )

    # Insert applications
    await Application.prisma().create_many(
        [
            {
                "name": "Availability Checker",
                "deleted": False,
                "userId": 1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Invoice Generator",
                "deleted": False,
                "userId": 1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Appointment Optimization Tool",
                "deleted": False,
                "userId": 1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Distance Calculator",
                "deleted": False,
                "userId": 1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Profile Management System",
                "deleted": False,
                "userId": 1,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Survey Tool",
                "deleted": False,
                "userId": 2,
                "updatedAt": datetime.now(),
            },
            {
                "name": "Scurvey Tool",
                "deleted": True,
                "userId": 2,
                "updatedAt": datetime.now(),
            },
        ]
    )


async def get_or_create_user_by_discord_id(discord_id: int) -> CodexUser:
    user = await CodexUser.prisma().find_unique_or_raise(
        where={"discord_id": str(discord_id)}
    )

    if not user:
        user = await CodexUser.prisma().create(discord_id=str(discord_id))

    return user


async def update_user(CodexUser: CodexUser) -> CodexUser:
    user = await CodexUser.prisma().update(
        where={"id": CodexUser.id},
        data=CodexUser.dict(),
    )

    return user


async def get_user(user_id: int) -> CodexUser:
    user = await CodexUser.prisma().find_unique_or_raise(where={"id": user_id})

    return user


async def list_users(page: int, page_size: int) -> UsersListResponse:
    # Calculate the number of items to skip
    skip = (page - 1) * page_size

    # Query the database for the total number of users
    total_items = await CodexUser.prisma().count()
    if total_items == 0:
        return UsersListResponse(
            users=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )

    # Query the database for users with pagination
    users = await CodexUser.prisma().find_many(skip=skip, take=page_size)

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
            id=CodexUser.id,
            discord_id=CodexUser.discord_id,
            createdAt=CodexUser.createdAt,
            email=CodexUser.email,
            name=CodexUser.name,
            role=CodexUser.role,
        )
        for CodexUser in users
    ]

    # Return both the users and the pagination info
    return UsersListResponse(users=user_responses, pagination=pagination)


async def get_app_by_id(user_id: int, app_id: int) -> ApplicationResponse:
    app = await Application.prisma().find_first_or_raise(
        where={
            "id": app_id,
            "userId": user_id,
        }
    )

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
    )


async def create_app(user_id: int, app_data: ApplicationCreate) -> ApplicationResponse:
    app = await Application.prisma().create(
        data={
            "name": app_data.name,
            "userId": user_id,
        }
    )

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userId,
    )


async def delete_app(user_id: int, app_id: int) -> None:
    await Application.prisma().update(
        where={
            "id": app_id,
            "userId": user_id,
        },
        data={"deleted": True},
    )


async def list_apps(
    user_id: int, page: int, page_size: int
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
                userid=app.userId,
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


async def get_deployment(deployment_id: int) -> DeploymentResponse:
    deployment = await Deployment.prisma().find_unique_or_raise(
        where={"id": deployment_id},
    )

    return DeliverableResponse(
        deployment=DeploymentMetadata(
            id=deployment.id,
            createdAt=deployment.createdAt,
            fileName=deployment.fileName,
            fileSize=deployment.fileSize,
            path=deployment.path,
        )
    )


async def delete_deployment(deployment_id: int) -> None:
    await Deployment.prisma().update(
        where={
            "id": deployment_id,
        },
        data={"deleted": True},
    )


async def list_deployments(
    user_id: int, deliverable_id: int, page: int, page_size: int
) -> DeploymentsListResponse:
    skip = (page - 1) * page_size

    total_items = await Deployment.count(
        where={
            "deliverable_id": deliverable_id,
            "userId": user_id,
        }
    )
    if total_items == 0:
        return DeploymentsListResponse(
            deployments=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )

    deployments = await Deployment.find_many(
        skip=skip,
        take=page_size,
        where={
            "deliverable_id": deliverable_id,
            "userId": user_id,
        },
    )

    total_pages = (total_items + page_size - 1) // page_size

    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    return DeploymentsListResponse(deployments=deployments, pagination=pagination)
