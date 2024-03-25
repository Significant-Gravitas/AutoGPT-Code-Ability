from typing import List, Tuple

from prisma.models import CompiledRoute, CompletedApp

from codex.api_model import Pagination
from codex.common.database import INCLUDE_API_ROUTE, INCLUDE_FUNC


async def get_deliverable(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str
) -> CompletedApp:
    completed_app = await CompletedApp.prisma().find_unique_or_raise(
        where={"id": deliverable_id, "deleted": False},
        include={"CompiledRoutes": True},
    )

    return completed_app


async def delete_deliverable(
    user_id: str, app_id: str, spec_id: str, deliverable_id: str
) -> None:
    await CompletedApp.prisma().update(
        where={"id": deliverable_id},
        data={"deleted": True},
    )


async def list_deliverables(
    user_id: str,
    app_id: str,
    spec_id: str,
    page: int = 1,
    page_size: int = 10,
) -> Tuple[List[CompletedApp], Pagination]:
    skip = (page - 1) * page_size
    total_items = await CompletedApp.prisma().count(
        where={"deleted": False, "specificationId": spec_id}
    )
    if total_items == 0:
        return [], Pagination(total_items=0, total_pages=0, current_page=0, page_size=0)
    total_pages = (total_items + page_size - 1) // page_size

    completed_apps_data = await CompletedApp.prisma().find_many(
        skip=skip,
        take=page_size,
        include={"CompiledRoutes": True},
        where={"deleted": False, "specificationId": spec_id},
    )

    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )
    return completed_apps_data, pagination


async def get_compiled_code(deliverable_id: str) -> list[str]:
    routes = await CompiledRoute.prisma().find_many(
        where={"completedAppId": deliverable_id}
    )
    return [route.compiledCode for route in routes]


async def get_compiled_route(compiled_route_id: str) -> CompiledRoute:
    return await CompiledRoute.prisma().find_unique_or_raise(
        where={"id": compiled_route_id},
        include={
            "RootFunction": INCLUDE_FUNC,  # type: ignore
            "Functions": INCLUDE_FUNC,  # type: ignore
            "ApiRouteSpec": INCLUDE_API_ROUTE,  # type: ignore
        },
    )
