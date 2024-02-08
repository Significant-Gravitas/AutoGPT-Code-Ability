from prisma import Prisma
from prisma.models import Application, CompletedApp, Deployment, Specification, User

from codex.api_model import (
    APIRouteSpecModel,
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
    ParamModel,
    RequestObjectModel,
    ResponseObjectModel,
    SpecificationResponse,
    SpecificationsListResponse,
    UserResponse,
    UsersListResponse,
)


async def get_or_create_user_by_discord_id(discord_id: int, db_client: Prisma) -> User:
    await db_client.connect()

    user = await db_client.user.upsert(
        where={
            "discord_id": discord_id,
        },
        data={
            "create": {"discord_id": discord_id},
            "update": {},
        },
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

    user = await User.prisma().find_unique_or_raise(where={"id": user_id})

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


async def get_app_by_id(
    user_id: int, app_id: int, db_client: Prisma
) -> ApplicationResponse:
    await db_client.connect()

    app = await Application.prisma().find_first_or_raise(
        where={
            "id": app_id,
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


async def create_app(
    user_id: int, app_data: ApplicationCreate, db_client: Prisma
) -> ApplicationResponse:
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
    try:
        await db_client.connect()
        await Application.prisma().update(
            where={
                "id": app_id,
                "userid": user_id,
            },
            data={"deleted": True},
        )

        await db_client.disconnect()
    except Exception as e:
        raise e


async def list_apps(
    user_id: int, page: int, page_size: int, db_client: Prisma
) -> ApplicationsListResponse:
    await db_client.connect()

    skip = (page - 1) * page_size
    total_items = await Application.count(where={"userid": user_id, "deleted": False})
    apps = await Application.prisma().find_many(
        where={"userid": user_id}, skip=skip, take=page_size
    )
    if apps:
        total_pages = (total_items + page_size - 1) // page_size

        await db_client.disconnect()

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


def map_spec_model_to_response(specification: Specification) -> SpecificationResponse:
    routes = []
    for route in specification.apiRoutes:
        routes.append(
            APIRouteSpecModel(
                id=route.id,
                createdAt=route.createdAt,
                method=route.method,
                path=route.path,
                description=route.description,
                requestObject=RequestObjectModel(
                    id=route.requestObject.id,
                    createdAt=route.requestObject.createdAt,
                    name=route.requestObject.name,
                    description=route.requestObject.description,
                    params=[
                        ParamModel(
                            id=param.id,
                            createdAt=param.createdAt,
                            name=param.name,
                            description=param.description,
                            param_type=param.param_type,
                        )
                        for param in route.requestObject.params
                    ],
                ),
                responseObject=ResponseObjectModel(
                    id=route.responseObject.id,
                    createdAt=route.responseObject.createdAt,
                    name=route.responseObject.name,
                    description=route.responseObject.description,
                    params=[
                        ParamModel(
                            id=param.id,
                            createdAt=param.createdAt,
                            name=param.name,
                            description=param.description,
                            param_type=param.param_type,
                        )
                        for param in route.responseObject.params
                    ],
                ),
            )
        )

    return SpecificationResponse(
        id=specification.id,
        createdAt=specification.createdAt,
        name=specification.name,
        context=specification.context,
        apiRoutes=routes,
    )


async def get_specification(
    user_id: int, app_id: int, spec_id: int, db_client: Prisma
) -> SpecificationResponse:
    await db_client.connect()

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
    await db_client.disconnect()
    return map_spec_model_to_response(specification)


async def delete_specification(spec_id: int, db_client: Prisma) -> Specification:
    try:
        await db_client.connect()
        await Specification.prisma().update(
            where={"id": spec_id},
            data={"deleted": True},
        )
        await db_client.disconnect()
    except Exception as e:
        raise e


async def list_specifications(
    user_id: int, app_id: int, page: int, page_size: int, db_client: Prisma
) -> SpecificationsListResponse:
    await db_client.connect()

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

        await db_client.disconnect()
        specs_response = [map_spec_model_to_response(spec) for spec in specs]

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
    await db_client.connect()
    completed_app = await CompletedApp.prisma().find_unique_or_raise(
        where={"id": deliverable_id},
        include={"compiledRoutes": True},
    )
    await db_client.disconnect()

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
    try:
        await db_client.connect()
        await CompletedApp.prisma().update(
            where={"id": deliverable_id},
            data={"deleted": True},
        )
        await db_client.disconnect()
    except Exception as e:
        raise e


async def list_deliverables(
    user_id: int,
    app_id: int,
    spec_id: int,
    page: int = 1,
    page_size: int = 10,
    db_client: Prisma = None,
) -> DeliverablesListResponse:
    await db_client.connect()

    skip = (page - 1) * page_size
    total_items = await CompletedApp.count()
    if total_items == 0:
        await db_client.disconnect()
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
    await db_client.disconnect()

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
    await db_client.connect()

    deployment = await Deployment.prisma().find_unique_or_raise(
        where={"id": deployment_id},
    )

    await db_client.disconnect()

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
    try:
        await db_client.connect()

        await Deployment.prisma().update(
            where={
                "id": deployment_id,
            },
            data={"deleted": True},
        )

        await db_client.disconnect()
    except Exception as e:
        raise e


async def list_deployments(
    user_id: int, deliverable_id: int, page: int, page_size: int, db_client: Prisma
) -> DeploymentsListResponse:
    await db_client.connect()

    skip = (page - 1) * page_size

    total_items = await Deployment.count(
        where={
            "deliverable_id": deliverable_id,
            "userId": user_id,
        }
    )
    if total_items == 0:
        await db_client.disconnect()
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

    await db_client.disconnect()

    return DeploymentsListResponse(deployments=deployments, pagination=pagination)
