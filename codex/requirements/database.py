import prisma
from prisma.models import Specification
from prisma.types import SpecificationCreateInput

import codex.requirements.agent_v2
from codex.api_model import (
    Identifiers,
    Pagination,
    SpecificationResponse,
    SpecificationsListResponse,
)
from codex.common.database import INCLUDE_API_ROUTE, INCLUDE_FIELD
from codex.common.model import ObjectTypeModel as ObjectTypeE
from codex.common.model import create_object_type
from codex.requirements.model import ApplicationRequirements


async def create_spec_v2(
    spec_holder: codex.requirements.agent_v2.SpecHolder,
) -> Specification:
    if spec_holder.ids.user_id is None:
        raise ValueError("User ID is required")

    if spec_holder.ids.app_id is None:
        raise ValueError("App ID is required")

    request_models = [
        r.request_model
        for m in spec_holder.modules
        for r in m.api_routes
        if r.request_model
    ]
    response_models = [
        r.response_model
        for m in spec_holder.modules
        for r in m.api_routes
        if r.response_model
    ]
    all_models = request_models + response_models

    created_objects = {}
    for model in all_models:
        created_objects = await create_object_type(model, created_objects)

    create_db = prisma.types.DatabaseSchemaCreateInput(
        name=spec_holder.db_response.database_schema.name,
        description=spec_holder.db_response.database_schema.description,
        DatabaseTables={
            "create": [
                {
                    "name": table.name,
                    "description": table.description,
                    "definition": table.definition,
                    "isEnum": False,
                }
                for table in spec_holder.db_response.database_schema.tables
            ]
            + [
                {
                    "name": enum.name,
                    "description": enum.description,
                    "definition": enum.definition,
                    "isEnum": True,
                }
                for enum in spec_holder.db_response.database_schema.enums
            ]
        },
    )

    create_modules = [
        prisma.types.ModuleCreateInput(
            name=m.name,
            description=m.description,
            ApiRouteSpecs={
                "create": [
                    {
                        "method": r.http_verb,
                        "path": r.path,
                        "functionName": r.function_name,
                        "AllowedAccessRoles": r.allowed_access_roles,
                        "description": r.description,
                        "RequestObject": {
                            "connect": {"id": created_objects[r.request_model.name].id}
                        }
                        if r.request_model
                        else None,
                        "ResponseObject": {
                            "connect": {"id": created_objects[r.response_model.name].id}
                        }
                        if r.response_model
                        else None,
                    }
                    for r in m.api_routes
                ]
            },
        )
        for m in spec_holder.modules
    ]

    create_spec = SpecificationCreateInput(
        Features={"connect": [{"id": f.id} for f in spec_holder.features]},
        DatabaseSchema={"create": create_db},
        Modules={"create": create_modules},
        User={"connect": {"id": spec_holder.ids.user_id}},
        Application={"connect": {"id": spec_holder.ids.app_id}},
    )

    spec = await Specification.prisma().create(
        data=create_spec,
        include={
            "Features": True,
            "DatabaseSchema": {"include": {"DatabaseTables": True}},
            "Modules": {
                "include": {
                    "ApiRouteSpecs": {
                        "include": {
                            "RequestObject": INCLUDE_FIELD,
                            "ResponseObject": INCLUDE_FIELD,
                        }
                    },
                },
            },
        },
    )

    return spec


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
                "name": route.database_schema.name,
                "description": route.database_schema.description,
                "DatabaseTables": {
                    "create": [
                        {
                            "name": table.name,
                            "description": table.description,
                            "definition": table.definition,
                            "isEnum": False,
                        }
                        for table in route.database_schema.tables
                    ]
                    + [
                        {
                            "name": enum.name,
                            "description": enum.description,
                            "definition": enum.definition,
                            "isEnum": True,
                        }
                        for enum in route.database_schema.enums
                    ]
                },
            }

        create_route = {
            "method": route.method,
            "path": route.path,
            "functionName": route.function_name,
            "AccessLevel": route.access_level.value,
            "description": route.description,
        }
        # [AGPT-593] Link the ObjectTypes to the route, if they exist and have fields.
        if route.request_model and route.request_model.Fields:
            create_route["RequestObject"] = {  # type: ignore
                "connect": {"id": created_objects[route.request_model.name].id}
            }
        if route.response_model and route.response_model.Fields:
            create_route["ResponseObject"] = {  # type: ignore
                "connect": {"id": created_objects[route.response_model.name].id}
            }
        if create_db:
            create_route["DatabaseSchema"] = {"create": create_db}  # type: ignore
        routes.append(create_route)

    create_spec = SpecificationCreateInput(
        name=spec.name,
        context=spec.context,
        ApiRouteSpecs={"create": routes},
    )
    if ids.interview_id:
        create_spec["Interview"] = {"connect": {"id": ids.interview_id}}
    if ids.user_id:
        create_spec["User"] = {"connect": {"id": ids.user_id}}
    if ids.app_id:
        create_spec["Application"] = {"connect": {"id": ids.app_id}}

    new_spec = await Specification.prisma().create(
        data=create_spec,
        include={"ApiRouteSpecs": INCLUDE_API_ROUTE},  # type: ignore
    )
    return new_spec


async def get_specification(user_id: str, app_id: str, spec_id: str) -> Specification:
    specification = await Specification.prisma().find_first_or_raise(
        where={
            "id": spec_id,
            "userId": user_id,
            "applicationId": app_id,
        },
        include={"ApiRouteSpecs": INCLUDE_API_ROUTE},  # type: ignore
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
        include={"ApiRouteSpecs": INCLUDE_API_ROUTE},  # type: ignore
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
            include={"ApiRouteSpecs": INCLUDE_API_ROUTE},  # type: ignore
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
