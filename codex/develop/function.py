"""
Function Helper Functions
"""

from prisma.enums import FunctionState
from prisma.models import ObjectType
from prisma.types import FunctionCreateInput

from codex.develop.model import FunctionDef


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
            for field in obj.Fields
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
