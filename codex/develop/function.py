"""
Function Helper Functions
"""

from prisma.enums import FunctionState
from prisma.models import ObjectType
from prisma.types import FunctionCreateInput, ObjectFieldCreateInput

from codex.common.model import get_related_types, normalize_type
from codex.develop.model import FunctionDef


async def construct_function(
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
        field = ObjectFieldCreateInput(
            name="return",
            description=function.return_desc,
            typeName=normalize_type(function.return_type),
            RelatedTypes={
                "connect": [
                    {"id": type.id}
                    for type in get_related_types(function.return_type, available_types)
                ]
            },
        )
        input["FunctionReturn"] = {"create": field}

    if function.arg_types:
        fields = [
            ObjectFieldCreateInput(
                name=name,
                description=function.arg_descs.get(name, "-"),
                typeName=normalize_type(type),
                RelatedTypes={
                    "connect": [
                        {"id": type.id}
                        for type in get_related_types(type, available_types)
                    ]
                },
            )
            for name, type in function.arg_types
        ]
        input["FunctionArgs"] = {"create": fields}

    return input


def generate_object_template(obj: ObjectType) -> str:
    fields = f"\n{' ' * 8}".join(
        [
            f"{field.name}: {field.typeName}  # {field.description}"
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
