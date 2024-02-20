from prisma.models import Specification

from codex.api_model import (
    Indentifiers,
    Pagination,
    SpecificationResponse,
    SpecificationsListResponse,
)
from codex.requirements.model import ApplicationRequirements


async def create_spec(
    ids: Indentifiers, spec: ApplicationRequirements
) -> Specification:
    routes = []

    if not spec.api_routes:
        raise ValueError("No routes found in the specification")
    for route in spec.api_routes:
        create_request = {
            "name": route.request_model.name,
            "description": route.request_model.description,
            "params": {
                "create": [
                    {
                        "name": param.name,
                        "description": param.description,
                        "param_type": param.param_type,
                    }
                    for param in route.request_model.params
                ],
            },
        }
        create_response = {
            "name": route.response_model.name,
            "description": route.response_model.description,
            "params": {
                "create": [
                    {
                        "name": param.name,
                        "description": param.description,
                        "param_type": param.param_type,
                    }
                    for param in route.response_model.params
                ],
            },
        }

        create_db = None
        if route.database_schema:
            create_db = {
                "description": route.database_schema.description,
                "tables": {
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
            "accessLevel": route.access_level.value,
            "description": route.description,
            "requestObjects": {"create": create_request},
            "responseObject": {"create": create_response},
        }
        if create_db:
            create_route["schemas"] = {"create": create_db}
        routes.append(create_route)

    create_spec = {
        "name": spec.name,
        "context": spec.context,
        "User": {"connect": {"id": ids.user_id}},
        "app": {"connect": {"id": ids.app_id}},
        "apiRoutes": {"create": routes},
    }
    import json

    with open("create.json", "w") as f:
        f.write(json.dumps(create_spec, indent=4))

    new_spec = await Specification.prisma().create(
        data=create_spec,
        include={
            "apiRoutes": {
                "include": {
                    "requestObjects": {"include": {"params": True}},
                    "responseObject": {"include": {"params": True}},
                    "schemas": {"include": {"tables": True}},
                }
            }
        },
    )
    return new_spec


async def get_specification(user_id: int, app_id: int, spec_id: int) -> Specification:
    specification = await Specification.prisma().find_first_or_raise(
        where={
            "id": spec_id,
            "userId": user_id,
            "applicationId": app_id,
        },
        include={
            "apiRoutes": {
                "include": {
                    "requestObjects": {"include": {"params": True}},
                    "responseObject": {"include": {"params": True}},
                }
            }
        },
    )

    return specification


async def delete_specification(spec_id: int) -> Specification:
    await Specification.prisma().update(
        where={"id": spec_id},
        data={"deleted": True},
    )


async def list_specifications(
    user_id: int, app_id: int, page: int, page_size: int
) -> SpecificationsListResponse:
    skip = (page - 1) * page_size
    total_items = await Specification.prisma().count(
        where={"userId": user_id, "applicationId": app_id, "deleted": False}
    )
    if total_items > 0:
        specs = await Specification.prisma().find_many(
            where={"userId": user_id, "applicationId": app_id, "deleted": False},
            include={
                "apiRoutes": {
                    "include": {
                        "requestObjects": {"include": {"params": True}},
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

        return SpecificationsListResponse(specs=specs_response, pagination=pagination)
    else:
        return SpecificationsListResponse(
            specs=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )
