"""
Function Helper Functions
"""

from prisma.enums import FunctionState
from prisma.models import ObjectType
from prisma.types import FunctionCreateInput

from codex.develop.model import FunctionDef


def get_type_children(type: str) -> (str, [str]):
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

    type1, children1 = get_type_children(type1)
    type2, children2 = get_type_children(type2)

    if type1 != type2:
        return False

    if len(children1) != len(children2):
        return False

    for c1, c2 in zip(children1, children2):
        if not is_type_equal(c1, c2):
            return False

    return True

def construct_function(
    function: FunctionDef, available_types: dict[str, ObjectType]
) -> FunctionCreateInput:
    input = FunctionCreateInput(
        functionName=function.name,
        template=function.function_template,
        description=function.function_desc,
        state=FunctionState.WRITTEN
        if function.is_implemented
        else FunctionState.DEFINITION,
        rawCode=function.function_code,
        functionCode=function.function_code,
    )

    if function.return_type:
        input["FunctionReturn"] = {
            "create": {
                "name": "return",
                "description": function.return_desc,
                "typeName": function.return_type,
                "typeId": available_types[function.return_type].id
                if function.return_type in available_types
                else None,
            }
        }

    if function.arg_types:
        input["FunctionArgs"] = {
            "create": [
                {
                    "name": name,
                    "description": function.arg_descs.get(name, "-"),
                    "typeName": type,
                    "typeId": available_types[type].id
                    if type in available_types
                    else None,
                }
                for name, type in function.arg_types
            ]
        }

    return input


def generate_object_template(obj: ObjectType) -> str:
    fields = f"\n{' ' * 8}".join(
        [
            f"{field.name}: {field.typeName} # {field.description}"
            for field in obj.Fields or []
        ]
    )
    template = f"""
    class {obj.name}(BaseModel):
        \"\"\"
        {obj.description}
        \"\"\"
        {fields}
    """
    return "\n".join([line[4:] for line in template.split("\n")]).strip()
