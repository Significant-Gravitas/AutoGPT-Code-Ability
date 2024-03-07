from typing import List, Optional, Tuple, __all__

from prisma.models import ObjectField, ObjectType
from pydantic import BaseModel, Field


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
    type: "str" = Field(
        description="The type of the field. Can be a string like List[str] or an use any of they related types like list[User]",
    )
    related_types: Optional[List[ObjectTypeModel]] = Field(
        description="The related types of the field", default=[]
    )


PYTHON_TYPES = set(__all__)
OPEN_BRACES = {"{": "Dict", "[": "List", "(": "Tuple"}
CLOSE_BRACES = {"}": "Dict", "]": "List", ")": "Tuple"}

RENAMED_TYPES = {
    "dict": "Dict",
    "list": "List",
    "tuple": "Tuple",
    "set": "Set",
    "frozenset": "FrozenSet",
    "type": "Type",
}


def unwrap_object_type(type: str) -> Tuple[str | None, List[str]]:
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

    type = type.replace(" ", "")

    def split_outer_level(type: str, separator: str) -> List[str]:
        brace_count = 0
        last_index = 0
        splits = []

        for i, c in enumerate(type):
            if c in OPEN_BRACES:
                brace_count += 1
            elif c in CLOSE_BRACES:
                brace_count -= 1
            elif c == separator and brace_count == 0:
                splits.append(type[last_index:i])
                last_index = i + 1

        splits.append(type[last_index:])
        return splits

    # Unwrap primitive union types
    union_split = split_outer_level(type, "|")
    if len(union_split) > 1:
        return "Union", union_split

    # Unwrap primitive dict/list/tuple types
    if type[0] in OPEN_BRACES and type[-1] in CLOSE_BRACES:
        type_name = OPEN_BRACES[type[0]]
        type_children = split_outer_level(type[1:-1], ",")
        return type_name, type_children

    brace_pos = type.find("[")
    if brace_pos != -1 and type[-1] == "]":
        # Unwrap normal composite types
        type_name = type[:brace_pos]
        type_children = split_outer_level(type[brace_pos + 1: -1], ",")
    else:
        # Non-composite types, no need to unwrap
        type_name = type
        type_children = []

    return RENAMED_TYPES.get(type_name, type_name), type_children


def is_type_equal(type1: str, type2: str) -> bool:
    """
    Check if two types are equal.
    This function handle composite types like list, dict, and tuple.
    group similar types like list[str], List[str], and [str] as equal.
    """

    type1, children1 = unwrap_object_type(type1)
    type2, children2 = unwrap_object_type(type2)

    if type1 != type2:
        return False

    if len(children1) != len(children2):
        return False

    if len(children1) == len(children2) == 0:
        return True

    for c1, c2 in zip(children1, children2):
        if not is_type_equal(c1, c2):
            return False

    return True

def get_typing_imports(object_types: list[str]) -> list[str]:
    typing_imports = {
        f"from typing import {extracted_type}"
        for object_type in object_types
        for extracted_type in extract_field_type(object_type)
        if extracted_type and extracted_type in PYTHON_TYPES
    }
    return sorted(typing_imports)


def extract_field_type(field_type: str) -> set[str]:
    """
    Extract the field type from a composite type.
    e.g. tuple[str, dict[str, int]] -> {str, int}

    Args:
        field_type (str): The field type to parse.
    Returns:
        list[str]: The extracted field types.
    """
    parent_type, children = unwrap_object_type(field_type)

    result = {parent_type}
    for child in children:
        result |= extract_field_type(child)

    return result

def normalize_type(type: str) -> str:
    """
    Normalize the type to a standard format.
    e.g. list[str] -> List[str], dict[str, int | float] -> Dict[str, Union[int, float]]

    Args:
        type (str): The type to normalize.
    Returns:
        str: The normalized type.
    """
    parent_type, children = unwrap_object_type(type)
    if len(children) == 0:
        return parent_type

    return f"{parent_type}[{', '.join([normalize_type(c) for c in children])}]"

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
                "typeName": normalize_type(type_name),
                "RelatedTypes": {
                    "connect": [
                        {"id": t.id}
                        for t in get_related_types(type_name, available_objects)
                    ]
                },
            }
        )

    typing_imports = get_typing_imports([f.type for f in object.Fields])

    created_object_type = await ObjectType.prisma().create(
        data={
            "name": object.name,
            "description": object.description,
            "Fields": {"create": field_inputs},
            "importStatements": typing_imports,
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
