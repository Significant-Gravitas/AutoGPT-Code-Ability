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


def generate_object_template(obj: ObjectType, force_generation=False) -> str:
    # If the object already has code, use it.
    if obj.code and not force_generation:
        return obj.code

    # Auto-generate a template for the object, this will not capture any class functions.
    fields = f"\n{' ' * 8}".join(
        [
            f"{field.name}: {field.typeName} "
            f"{('= '+field.value) if field.value else ''} "
            f"{('# '+field.description) if field.description else ''}"
            for field in obj.Fields or []
        ]
    )

    parent_class = ""
    if obj.isEnum:
        parent_class = "Enum"
    elif obj.isPydantic:
        parent_class = "BaseModel"

    template = f"""
    class {obj.name}({parent_class}):
        \"\"\"
        {obj.description}
        \"\"\"
        {fields}
    """
    return "\n".join([line[4:] for line in template.split("\n")]).strip()
