from typing import List, Optional
from pydantic import BaseModel, Field
from prisma.models import ObjectType, ObjectField


class ObjectTypeModel(BaseModel):
    name: str = Field(description="The name of the object")
    description: Optional[str] = Field(
        description="The description of the object", default=None
    )
    Fields: Optional[List["ObjectFieldModel"]] = Field(
        description="The fields of the object", default=None
    )
    is_pydantic: bool = Field(
        description="Whether the object is a pydantic model", default=True
    )
    is_implemented: bool = Field(
        description="Whether the object is implemented", default=True
    )


class ObjectFieldModel(BaseModel):
    name: str = Field(description="The name of the field")
    description: Optional[str] = Field(
        description="The description of the field", default=None
    )
    type: "ObjectTypeModel | str" = Field(
        description="The type of the field. Can be a string like List[str] or an "
        "ObjectTypeModel"
    )


def unwrap_object_type(type: str) -> (str, [str]):
    """
    Get the type and children of a composite type.
    Args:
        type (str): The type to parse.
    Returns:
        str: The type.
        [str]: The children types.
    """
    if type is None:
        return None, []
    if "list[" in type.lower():
        return "list", [type[5:-1]]
    if "[" == type[0] and "]" == type[-1]:
        return "list", [type[1:-1]]
    if "dict[" in type.lower():
        return "dict", type[5:-1].split(",")
    if "tuple[" in type.lower():
        return "tuple", type[6:-1].split(",")
    if "(" == type[0] and ")" == type[-1]:
        return "tuple", type[1:-1].split(",")
    if "str" == type or "String" == type:
        return "str", []
    if "int" == type or "Int" == type:
        return "int", []
    if "float" == type or "Float" == type:
        return "float", []
    if "bool" == type or "Boolean" == type:
        return "bool", []
    if "any" == type or "Any" == type:
        return "any", []
    return type, []


def is_type_equal(type1: str, type2: str) -> bool:
    """
    Check if two types are equal.
    This function handle composite types like list, dict, and tuple.
    group similar types like list[str], List[str], and [str] as equal.
    """
    type1 = type1.replace(" ", "")
    type2 = type2.replace(" ", "")
    if type1 == type2:
        return True

    type1, children1 = unwrap_object_type(type1)
    type2, children2 = unwrap_object_type(type2)

    if type1 != type2:
        return False

    if len(children1) != len(children2):
        return False

    for c1, c2 in zip(children1, children2):
        if not is_type_equal(c1, c2):
            return False

    return True


def extract_field_type(field_type: str) -> list[str]:
    """
    Extract the field type from a composite type.
    e.g. tuple[str, dict[str, int]] -> [str, str, int]

    Args:
        field_type (str): The field type to parse.
    Returns:
        list[str]: The extracted field types.
    """
    parent_type, children = unwrap_object_type(field_type)
    if len(children) == 0:
        return [parent_type]

    result = []
    for child in children:
        result.extend(extract_field_type(child))
    return result


def get_related_types(
    type: str, available_objects: dict[str, ObjectType]
) -> list[ObjectType]:
    """
    Get the related types of a composite type.
    e.g. tuple[Obj1, dict[Obj2, Obj3]] with {Obj1, Obj3} -> [Obj1, Obj3]

    Args:
        type (str): The type to parse.
        available_objects (dict[str, ObjectType]): The available objects.

    Returns:
        list[ObjectType]: The related types.
    """
    return [
        available_objects[related_type]
        for related_type in extract_field_type(type)
        if related_type in available_objects
    ]


async def create_object_type(
    object: ObjectTypeModel,
    available_objects: dict[str, ObjectType],
) -> dict[str, ObjectType]:
    """
    Creates and store object types in the database.

    Args:
    object (ObjectTypeModel): The object to create.
    available_objects (dict[str, ObjectType]):
        The set of object definitions that have already been created.
        This will be used to link the related object fields and avoid duplicates.

    Returns:
        dict[str, ObjectType]: Updated available_objects with the newly created objects.
    """
    if object.name in available_objects:
        return available_objects

    field_inputs = []
    for field in object.Fields:
        if isinstance(field.type, ObjectTypeModel):
            available_objects = await create_object_type(field.type, available_objects)
            type_name = field.type.name
        else:
            type_name = field.type

        field_inputs.append(
            {
                "name": field.name,
                "description": field.description,
                "typeName": type_name,
                "RelatedTypes": {
                    "connect": [
                        {"id": t.id}
                        for t in get_related_types(type_name, available_objects)
                    ]
                },
            }
        )

    created_object_type = await ObjectType.prisma().create(

        data={
            "name": object.name,
            "description": object.description,
            "Fields": {"create": field_inputs},
        },
        include={"Fields": {"include": {"RelatedTypes": True}}},
    )
    available_objects[object.name] = created_object_type

    # Connect the fields of available objects to the newly created object.
    # Naively check each available object if it has a related field to the new object.
    # TODO(majdyz): Optimize this step if needed.
    for obj in available_objects.values():
        for field in obj.Fields:
            if object.name not in extract_field_type(field.typeName):
                continue
            if object.name in [f.typeName for f in field.RelatedTypes]:
                continue

            # Link created_object_type.id to the field.RelatedTypes
            reltypes = get_related_types(field.typeName, available_objects)
            field.RelatedTypes = (
                await ObjectField.prisma()
                .update(
                    where={"id": field.id},
                    data={
                        "RelatedTypes": {"connect": [{"id": t.id} for t in reltypes]}
                    },
                    include={"RelatedTypes": True},
                )
                .RelatedTypes
            )

    return available_objects
