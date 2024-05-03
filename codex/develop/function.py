"""
Function Helper Functions
"""

import logging

from prisma.enums import FunctionState
from prisma.models import ObjectType
from prisma.types import FunctionCreateInput, ObjectFieldCreateInput

from codex.common.model import (
    FunctionDef,
    ObjectTypeModel,
    get_related_types,
    normalize_type,
)

logger = logging.getLogger(__name__)


async def construct_function(
    function: FunctionDef, available_types: dict[str, ObjectType]
) -> FunctionCreateInput:
    if not function.function_template:
        raise ValueError("Function template is required")

    input = FunctionCreateInput(
        functionName=function.name,
        template=function.function_template or "",
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
        input["FunctionArgs"] = {"create": fields}  # type: ignore

    return input


def generate_object_code(obj: ObjectTypeModel) -> str:
    if not obj.name:
        return ""  # Avoid generating an empty object

    # Auto-generate a template for the object, this will not capture any class functions.
    fields = f"\n{' ' * 4}".join(
        [
            f"{field.name}: {field.type} "
            f"{('= '+field.value) if field.value else ''} "
            f"{('# '+field.description) if field.description else ''}"
            for field in obj.Fields or []
        ]
    )

    parent_class = ""
    if obj.is_enum:
        parent_class = "Enum"
    elif obj.is_pydantic:
        parent_class = "BaseModel"

    doc_string = (
        f"""\"\"\"
    {obj.description}
    \"\"\""""
        if obj.description
        else ""
    )

    method_body = ("\n" + " " * 4).join(obj.code.split("\n")) + "\n" if obj.code else ""

    template = f"""
class {obj.name}({parent_class}):
    {doc_string if doc_string else ""}
    {fields if fields else ""}
    {method_body if method_body else ""}
    {"pass" if not fields and not method_body else ""}
"""
    return "\n".join(line for line in template.split("\n")).strip()


def generate_object_template(obj: ObjectType) -> str:
    return generate_object_code(ObjectTypeModel(db_obj=obj))
