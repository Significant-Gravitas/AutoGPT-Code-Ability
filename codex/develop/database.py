from typing import List, Tuple

from prisma.models import CompletedApp, ObjectType

from codex.develop.model import ObjectDef
from codex.api_model import Pagination


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


async def create_object_type(
    object: ObjectDef,
    available_objects: dict[str, ObjectType],
) -> dict[str, ObjectType]:
    """
    Creates and store object types in the database.

    Args:
    objects (ObjectDef): The object definitions to be created.
    available_objects (dict[str, ObjectType]):
        The set of object definitions that have already been created.
        This will be used to link the related object fields and avoid duplicates.

    Returns:
        dict[str, ObjectType]: Updated available_objects with the newly created objects.
    """
    if object.name in available_objects:
        return available_objects

    available_objects[object.name] = await ObjectType.prisma().create(
        data={
            "name": object.name,
            "Fields": {
                "create": [
                    {
                        "name": field_name,
                        "typeName": field_type,
                        "typeId": available_objects[field_type].id
                        if field_type in available_objects
                        else None,
                    }
                    for field_name, field_type in object.fields.items()
                ]
            },
        },
        include={"Fields": True},
    )
    # TODO(majdyz): connect the fields of available objects to the newly created object.

    return available_objects
