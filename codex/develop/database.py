import asyncio

from typing import List, Tuple

from prisma.models import CompletedApp, ObjectType, ObjectField

from codex.develop.function import get_type_children
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

    def extract_field_type(field_type: str) -> str:
        parent_type, children = get_type_children(field_type)
        if len(children) == 0:
            return parent_type
        return extract_field_type(children[-1])

    fields = []
    for field_name, field_type in object.fields.items():
        field = {
            "name": field_name,
            "typeName": field_type,
        }
        related_field = extract_field_type(field_type)
        if related_field in available_objects:
            field["typeId"] = available_objects[related_field].id
        fields.append(field)

    available_objects[object.name] = await ObjectType.prisma().create(
        data={"name": object.name, "Fields": {"create": fields}},
        include={"Fields": True},
    )

    # Connect the fields of available objects to the newly created object.
    # Naively check each available object if it has a related field to the new object.
    # TODO(majdyz): Optimize this step if needed.
    updates = []
    for obj in available_objects.values():
        for field in obj.Fields:
            if field.typeId is not None:
                continue
            if object.name != extract_field_type(field.typeName):
                continue
            field.typeId = available_objects[object.name].id

            updates.append(ObjectField.prisma().update(
                where={"id": field.id},
                data={"typeId": field.typeId},
            ))
    asyncio.gather(*updates)

    return available_objects
