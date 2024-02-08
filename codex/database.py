from prisma import Prisma
from prisma.models import Application, CompletedApp, Deployment, Specification, User

from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationsListResponse,
    CompiledRouteModel,
    CompletedAppModel,
    DeliverableResponse,
    DeliverablesListResponse,
    DeploymentMetadata,
    DeploymentResponse,
    DeploymentsListResponse,
    Pagination,
    SpecificationResponse,
    SpecificationsListResponse,
    UserResponse,
    UsersListResponse,
)


async def get_or_create_user_by_discord_id(discord_id: int, db_client: Prisma) -> User:
    user = await db_client.user.upsert(
        where={
            "discord_id": discord_id,
        },
        data={
            "create": {"discord_id": discord_id},
            "update": {},
        },
    )

    return user


async def update_user(user: User, db_client: Prisma) -> User:
    user = await User.prisma().update(
        where={"id": user.id},
        data=user.dict(),
    )

    return user


async def get_user(user_id: int, db_client: Prisma) -> User:
    user = await User.prisma().find_unique_or_raise(where={"id": user_id})

    return user


async def list_users(page: int, page_size: int, db_client: Prisma) -> UsersListResponse:
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


async def get_app_by_id(
    user_id: int, app_id: int, db_client: Prisma
) -> ApplicationResponse:
    app = await Application.prisma().find_first_or_raise(
        where={
            "id": app_id,
            "userid": user_id,
        }
    )

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userid,
    )


async def create_app(
    user_id: int, app_data: ApplicationCreate, db_client: Prisma
) -> ApplicationResponse:
    app = await Application.prisma().create(
        data={
            "name": app_data.name,
            "userid": user_id,
        }
    )

    return ApplicationResponse(
        id=app.id,
        createdAt=app.createdAt,
        updatedAt=app.updatedAt,
        name=app.name,
        userid=app.userid,
    )


async def delete_app(user_id: int, app_id: int, db_client: Prisma) -> None:
    await Application.prisma().update(
        where={
            "id": app_id,
            "userid": user_id,
        },
        data={"deleted": True},
    )


async def list_apps(
    user_id: int, page: int, page_size: int, db_client: Prisma
) -> ApplicationsListResponse:
    skip = (page - 1) * page_size
    total_items = await Application.count(where={"userid": user_id, "deleted": False})
    apps = await Application.prisma().find_many(
        where={"userid": user_id}, skip=skip, take=page_size
    )
    if apps:
        total_pages = (total_items + page_size - 1) // page_size

        applications_response = [
            ApplicationResponse(
                id=app.id,
                createdAt=app.createdAt,
                updatedAt=app.updatedAt,
                name=app.name,
                userid=app.userid,
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


async def get_specification(
    user_id: int, app_id: int, spec_id: int, db_client: Prisma
) -> SpecificationResponse:
    specification = await Specification.prisma().find_first(
        where={
            "id": spec_id,
            "userId": user_id,
            "appId": app_id,
        },
        include={
            "apiRoutes": {
                "include": {
                    "requestObject": {"include": {"params": True}},
                    "responseObject": {"include": {"params": True}},
                }
            }
        },
    )

    return SpecificationResponse.from_specification(specification)


async def delete_specification(spec_id: int, db_client: Prisma) -> Specification:
    await Specification.prisma().update(
        where={"id": spec_id},
        data={"deleted": True},
    )


async def list_specifications(
    user_id: int, app_id: int, page: int, page_size: int, db_client: Prisma
) -> SpecificationsListResponse:
    skip = (page - 1) * page_size
    total_items = await Specification.count(
        where={"userid": user_id, "appId": app_id, "deleted": False}
    )
    if total_items > 0:
        specs = await Specification.prisma().find_many(
            where={"userid": user_id},
            include={
                "apiRoutes": {
                    "include": {
                        "requestObject": {"include": {"params": True}},
                        "responseObject": {"include": {"params": True}},
                    }
                }
            },
            skip=skip,
            take=page_size,
        )

        total_pages = (total_items + page_size - 1) // page_size

        specs_response = [
            SpecificationResponse.from_specification(spec) for spec in specs
        ]

        pagination = Pagination(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )

        return SpecificationResponse(specs=specs_response, pagination=pagination)
    else:
        return SpecificationsListResponse(
            specs=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )


async def get_deliverable(
    db_client: Prisma, user_id: int, app_id: int, spec_id: int, deliverable_id: int
) -> DeliverableResponse:
    completed_app = await CompletedApp.prisma().find_unique_or_raise(
        where={"id": deliverable_id},
        include={"compiledRoutes": True},
    )

    return DeliverableResponse(
        completedApp=CompletedAppModel(
            id=completed_app.id,
            createdAt=completed_app.createdAt,
            name=completed_app.name,
            description=completed_app.description,
            compiledRoutes=[
                CompiledRouteModel(**route.dict())
                for route in completed_app.compiledRoutes
            ],
            databaseSchema=completed_app.databaseSchema,
        )
    )


async def delete_deliverable(
    db_client: Prisma, user_id: int, app_id: int, spec_id: int, deliverable_id: int
) -> None:
    await CompletedApp.prisma().update(
        where={"id": deliverable_id},
        data={"deleted": True},
    )


async def list_deliverables(
    user_id: int,
    app_id: int,
    spec_id: int,
    page: int = 1,
    page_size: int = 10,
    db_client: Prisma = None,
) -> DeliverablesListResponse:
    skip = (page - 1) * page_size
    total_items = await CompletedApp.count()
    if total_items == 0:
        return DeliverablesListResponse(
            completedApps=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )
    total_pages = (total_items + page_size - 1) // page_size

    completed_apps_data = await CompletedApp.prisma().find_many(
        skip=skip,
        take=page_size,
        include={"compiledRoutes": True},
    )

    completed_apps = [
        CompletedAppModel(
            id=app.id,
            createdAt=app.createdAt,
            name=app.name,
            description=app.description,
            compiledRoutes=[
                CompiledRouteModel(**route.dict()) for route in app.compiledRoutes
            ],
            databaseSchema=app.databaseSchema,
        )
        for app in completed_apps_data
    ]

    return DeliverablesListResponse(
        completedApps=completed_apps,
        pagination=Pagination(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        ),
    )


async def get_deployment(deployment_id: int, db_client: Prisma) -> DeploymentResponse:
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


async def delete_deployment(deployment_id: int, db_client: Prisma) -> None:
    await Deployment.prisma().update(
        where={
            "id": deployment_id,
        },
        data={"deleted": True},
    )


async def list_deployments(
    user_id: int, deliverable_id: int, page: int, page_size: int, db_client: Prisma
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
