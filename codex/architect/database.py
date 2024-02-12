from prisma.models import CompletedApp

from codex.api_model import (
    CompiledRouteModel,
    CompletedAppModel,
    DeliverableResponse,
    DeliverablesListResponse,
    Pagination,
)


async def get_deliverable(
    user_id: int, app_id: int, spec_id: int, deliverable_id: int
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
    user_id: int, app_id: int, spec_id: int, deliverable_id: int
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
