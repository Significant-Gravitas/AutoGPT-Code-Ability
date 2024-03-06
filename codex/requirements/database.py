from prisma.models import Specification
from prisma.types import SpecificationCreateInput

from codex.api_model import (
    Identifiers,
    Pagination,
    SpecificationResponse,
    SpecificationsListResponse,
)
from codex.common.model import ObjectTypeModel as ObjectTypeE, create_object_type
from codex.requirements.model import ApplicationRequirements


async def create_spec(ids: Identifiers, spec: ApplicationRequirements) -> Specification:
    routes = []

    if ids.user_id is None:
        raise ValueError("User ID is required")
    if ids.app_id is None:
        raise ValueError("App ID is required")

    if not spec.api_routes:
        raise ValueError("No routes found in the specification")

    # TODO(ntindle): review and refactor this logic persisting ObjectType.
    #   For loop can be converted into a batch query or at least an async tasks.

    # Persist all ObjectTypes from the spec
    all_models: list[ObjectTypeE] = [
        route.request_model for route in spec.api_routes if route
    ] + [route.response_model for route in spec.api_routes if route]

    created_objects = {}
    for model in all_models:
        created_objects = await create_object_type(model, created_objects)

    # Persist all routes from the spec
    for route in spec.api_routes:
        create_db = None
        if route.database_schema:
            create_db = {
                "description": route.database_schema.description,
                "DatabaseTables": {
                    "create": [
                        {
                            "description": table.description,
                            "definition": table.definition,
                        }
                        for table in route.database_schema.tables
                    ],
                },
            }
        create_route = {
            "method": route.method,
            "path": route.path,
            "functionName": route.function_name,
            "AccessLevel": route.access_level.value,
            "description": route.description,
        }
        if route.request_model:
            create_route["RequestObject"] = {
                "connect": {"id": created_objects[route.request_model.name].id}
            }
        if route.response_model:
            create_route["ResponseObject"] = {
                "connect": {"id": created_objects[route.response_model.name].id}
            }
        if create_db:
            create_route["DatabaseSchema"] = {"create": create_db}
        routes.append(create_route)

    create_spec = SpecificationCreateInput(
        name=spec.name,
        context=spec.context,
        User={"connect": {"id": ids.user_id}},
        Application={"connect": {"id": ids.app_id}},
        ApiRouteSpecs={"create": routes},
    )

    new_spec = await Specification.prisma().create(
        data=create_spec,
        include={
            "ApiRouteSpecs": {
                "include": {
                    "RequestObject": {"include": {"Fields": True}},
                    "ResponseObject": {"include": {"Fields": True}},
                    "DatabaseSchema": {"include": {"DatabaseTables": True}},
                }
            }
        },
    )
    return new_spec


async def get_specification(user_id: str, app_id: str, spec_id: str) -> Specification:
    specification = await Specification.prisma().find_first_or_raise(
        where={
            "id": spec_id,
            "userId": user_id,
            "applicationId": app_id,
        },
        include={
            "ApiRouteSpecs": {
                "include": {
                    "RequestObject": {"include": {"Fields": True}},
                    "ResponseObject": {"include": {"Fields": True}},
                }
            }
        },
    )

    return specification


async def get_latest_specification(user_id: str, app_id: str) -> Specification:
    """
    Gets the latest specification for the given user and app

    Args:
        user_id (str): uuid of the user
        app_id (str): uuid of the application

    Returns:
        str: uuid of the latest specification for the user and app
    """
    specification = await Specification.prisma().find_many(
        where={
            "userId": user_id,
            "applicationId": app_id,
            "deleted": False,
        },
        include={
            "ApiRouteSpecs": {
                "include": {
                    "RequestObject": {"include": {"Fields": True}},
                    "ResponseObject": {"include": {"Fields": True}},
                }
            }
        },
        order={"createdAt": "desc"},
    )
    if not specification:
        raise ValueError("No specifications found for the user and app")

    return specification[0]


async def delete_specification(spec_id: str) -> None:
    await Specification.prisma().update(
        where={"id": spec_id},
        data={"deleted": True},
    )


async def list_specifications(
    user_id: str, app_id: str, page: int, page_size: int
) -> SpecificationsListResponse:
    skip = (page - 1) * page_size
    total_items = await Specification.prisma().count(
        where={"userId": user_id, "applicationId": app_id, "deleted": False}
    )
    if total_items > 0:
        specs = await Specification.prisma().find_many(
            where={"userId": user_id, "applicationId": app_id, "deleted": False},
            include={
                "ApiRouteSpecs": {
                    "include": {
                        "RequestObject": {"include": {"Fields": True}},
                        "ResponseObject": {"include": {"Fields": True}},
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

        return SpecificationsListResponse(specs=specs_response, pagination=pagination)
    else:
        return SpecificationsListResponse(
            specs=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )
