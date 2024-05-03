from typing import List, Tuple

from prisma.models import (
    CompiledRoute,
    CompletedApp,
    Function,
    ObjectType,
    Specification,
)

from codex.api_model import Identifiers, Pagination
from codex.common.database import INCLUDE_API_ROUTE, INCLUDE_FUNC


async def get_deliverable(deliverable_id: str) -> CompletedApp:
    completed_app = await CompletedApp.prisma().find_unique_or_raise(
        where={"id": deliverable_id, "deleted": False},
        include={
            "CompiledRoutes": {
                "include": {
                    "RootFunction": INCLUDE_FUNC,  # type: ignore
                    "Functions": INCLUDE_FUNC,
                    "ApiRouteSpec": INCLUDE_API_ROUTE,
                }
            }
        },
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


async def get_ids_from_function_id_and_compiled_route(
    function_id: str, compiled_route_id: str
) -> Identifiers:
    function = await Function.prisma().find_unique_or_raise(
        where={"id": function_id},
        include={
            "CompiledRoute": {
                "include": {
                    "ApiRouteSpec": True,
                    "CompletedApp": {
                        "include": {
                            "User": True,
                            "Application": True,
                            "Specification": True,
                        },
                    },
                },
            },
        },
    )

    compiled_route = await CompiledRoute.prisma().find_unique_or_raise(
        where={"id": compiled_route_id},
        include={
            "CompletedApp": {
                "include": {"User": True, "Application": True, "Specification": True},
            }
        },
    )
    if not compiled_route.CompletedApp:
        raise ValueError("Compiled route does not have a completed app")
    if not compiled_route.CompletedApp.Specification:
        raise ValueError("Compiled route does not have a specification")
    specification = await Specification.prisma().find_unique_or_raise(
        where={"id": compiled_route.CompletedApp.Specification.id},
        include={
            "Interview": True,
            "User": True,
        },
    )
    if not specification.User:
        raise ValueError("Specification does not have a user")
    return Identifiers(
        user_id=specification.userId,
        cloud_services_id=specification.User.cloudServicesId,
        app_id=specification.applicationId,
        interview_id=specification.interviewId,
        spec_id=specification.id,
        compiled_route_id=function.compiledRouteId,
        function_id=function.id,
        completed_app_id=compiled_route.completedAppId,
    )


async def get_object_type_referred_functions(object_type_id: str) -> list[str]:
    referred_object_fields = await ObjectType.prisma().find_first_or_raise(
        where={"id": object_type_id},
        include={
            "ReferredRequestAPIRoutes": True,
            "ReferredResponseAPIRoutes": True,
        },
    )
    functions_on_request = referred_object_fields.ReferredRequestAPIRoutes or []
    functions_on_response = referred_object_fields.ReferredResponseAPIRoutes or []
    referred_functions = []
    for route in functions_on_request + functions_on_response:
        referred_functions.append(route.functionName)
    return referred_functions
