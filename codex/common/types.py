from typing import List, Tuple

from prisma.models import ObjectType

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


def unwrap_object_type(type: str) -> Tuple[str, List[str]]:
    """
    Get the type and children of a composite type.
    Args:
        type (str): The type to parse.
    Returns:
        str: The type.
        [str]: The children types.
    """
    type = type.replace(" ", "")
    if not type:
        return "", []

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
        if len(union_split) == 2 and "None" in union_split:
            return "Optional", [v for v in union_split if v != "None"]
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
        type_children = split_outer_level(type[brace_pos + 1 : -1], ",")
    else:
        # Non-composite types, no need to unwrap
        type_name = type
        type_children = []

    return RENAMED_TYPES.get(type_name, type_name), type_children


def is_type_equal(type1: str | None, type2: str | None) -> bool:
    """
    Check if two types are equal.
    This function handle composite types like list, dict, and tuple.
    group similar types like list[str], List[str], and [str] as equal.
    """
    if type1 is None and type2 is None:
        return True
    if type1 is None or type2 is None:
        return False

    evaluated_type1, children1 = unwrap_object_type(type1)
    evaluated_type2, children2 = unwrap_object_type(type2)

    # Compare the class name of the types (ignoring the module)
    # TODO(majdyz): compare the module name as well.
    t_len = min(len(evaluated_type1), len(evaluated_type2))
    if evaluated_type1.split(".")[-t_len:] != evaluated_type2.split(".")[-t_len:]:
        return False

    if len(children1) != len(children2):
        return False

    if len(children1) == len(children2) == 0:
        return True

    for c1, c2 in zip(children1, children2):
        if not is_type_equal(c1, c2):
            return False

    return True


def extract_field_type(field_type: str | None) -> set[str]:
    """
    Extract the field type from a composite type.
    e.g. tuple[str, dict[str, int]] -> {tuple, dict, str, int}

    Args:
        field_type (str): The field type to parse.
    Returns:
        list[str]: The extracted field types.
    """
    if field_type is None:
        return set()
    parent_type, children = unwrap_object_type(field_type)

    result = {parent_type}
    for child in children:
        result |= extract_field_type(child)
    return result


def normalize_type(type: str, renamed_types: dict[str, str] = {}) -> str:
    """
    Normalize the type to a standard format.
    e.g. list[str] -> List[str], dict[str, int | float] -> Dict[str, Union[int, float]]

    Args:
        type (str): The type to normalize.
    Returns:
        str: The normalized type.
    """
    parent_type, children = unwrap_object_type(type)

    if parent_type in renamed_types:
        parent_type = renamed_types[parent_type]

    if len(children) == 0:
        return parent_type

    return f"{parent_type}[{', '.join([normalize_type(c, renamed_types) for c in children])}]"


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
