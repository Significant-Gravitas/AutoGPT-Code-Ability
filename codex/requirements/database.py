import asyncio
import os
import pickle

import prisma
from prisma.models import Specification
from prisma.types import SpecificationCreateInput

import codex.requirements.agent
from codex.api_model import (
    Pagination,
    SpecificationResponse,
    SpecificationsListResponse,
)
from codex.common.database import INCLUDE_API_ROUTE
from codex.common.model import create_object_type


async def create_specification(
    spec_holder: codex.requirements.agent.SpecHolder,
) -> Specification:
    if spec_holder.ids.user_id is None:
        raise ValueError("User ID is required")

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

    create_db: prisma.types.DatabaseSchemaCreateInput | None = None

    if spec_holder.db_response and spec_holder.db_response.database_schema:
        create_database_table = []
        for table in spec_holder.db_response.database_schema.tables:
            create_database_table.append(
                prisma.types.DatabaseTableCreateInput(
                    name=table.name,
                    description=table.description,
                    definition=table.definition,
                )
            )
        for enum in spec_holder.db_response.database_schema.enums:
            create_database_table.append(
                prisma.types.DatabaseTableCreateInput(
                    name=enum.name,
                    description=enum.description,
                    definition=enum.definition,
                    isEnum=True,
                )
            )

        create_db = prisma.types.DatabaseSchemaCreateInput(
            name=spec_holder.db_response.database_schema.name,
            description=spec_holder.db_response.database_schema.description,
            DatabaseTables={"create": create_database_table},
        )

    create_modules = []
    for module in spec_holder.modules:
        api_routes = []
        for r in module.api_routes:
            create_route = {
                "method": r.http_verb,
                "path": r.path,
                "functionName": r.function_name,
                "AllowedAccessRoles": r.allowed_access_roles,
                "description": r.description,
                "AccessLevel": r.access_level,
            }

            if r.request_model:
                create_route["RequestObject"] = {
                    "connect": {"id": created_objects[r.request_model.name].id}
                }
            if r.response_model:
                create_route["ResponseObject"] = {
                    "connect": {"id": created_objects[r.response_model.name].id}
                }
            api_routes.append(create_route)
        create_modules.append(
            prisma.types.ModuleCreateInput(
                name=module.name,
                description=module.description,
                interactions=module.interactions,
                ApiRouteSpecs={"create": api_routes},
            )
        )

    create_spec_dict = {}
    if spec_holder.features:
        create_spec_dict["Features"] = {
            "connect": [{"id": f.id} for f in spec_holder.features]
        }
    if create_modules:
        create_spec_dict["Modules"] = {"create": create_modules}
    if create_db:
        create_spec_dict["DatabaseSchema"] = {"create": create_db}
    if spec_holder.ids.user_id:
        create_spec_dict["User"] = {"connect": {"id": spec_holder.ids.user_id}}
    if spec_holder.ids.app_id:
        create_spec_dict["Application"] = {"connect": {"id": spec_holder.ids.app_id}}
    if spec_holder.ids.interview_id:
        create_spec_dict["Interview"] = {
            "connect": {"id": spec_holder.ids.interview_id}
        }

    create_spec = SpecificationCreateInput(**create_spec_dict)

    include_objs = prisma.types.SpecificationInclude(
        Features=True,
        DatabaseSchema={"include": {"DatabaseTables": True}},
        Modules={"include": {"ApiRouteSpecs": INCLUDE_API_ROUTE}},  # type: ignore
    )

    spec = await Specification.prisma().create(
        data=create_spec,
        include=include_objs,
    )

    return spec


async def get_specification(user_id: str, app_id: str, spec_id: str) -> Specification:
    specification = await Specification.prisma().find_first_or_raise(
        where={
            "id": spec_id,
            "userId": user_id,
            "applicationId": app_id,
        },
        include={
            "Modules": {"include": {"ApiRouteSpecs": INCLUDE_API_ROUTE}},
            "DatabaseSchema": {
                "include": {
                    "DatabaseTables": True,
                }
            },
            "Features": True,
            # type: ignore
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
            "Modules": {"include": {"ApiRouteSpecs": INCLUDE_API_ROUTE}},
            "DatabaseSchema": {
                "include": {
                    "DatabaseTables": True,
                }
            },
            "Features": True,
            # type: ignore
        },
        order={"createdAt": "desc"},
    )
    if not specification:
        raise ValueError("No specifications found for the user and app")

    return specification[0]


async def connect_db_schema_to_specification(spec_id: str, db_schema_id: str) -> str:
    await Specification.prisma().update(
        where={"id": spec_id},
        data={"DatabaseSchema": {"connect": {"id": db_schema_id}}},
    )
    return db_schema_id


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
                "Modules": {"include": {"ApiRouteSpecs": INCLUDE_API_ROUTE}},
                "DatabaseSchema": {
                    "include": {
                        "DatabaseTables": True,
                    }
                },
                "Features": True,
                # type: ignore
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


async def main():
    file_path = os.path.join(os.path.dirname(__file__), "spec_holder.pickle")
    prisma_client = prisma.Prisma(auto_register=True)
    await prisma_client.connect()
    with open(file_path, "rb") as file:
        spec_holder = pickle.load(file)

    await create_specification(spec_holder)
    await prisma_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
