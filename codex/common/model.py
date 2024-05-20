import datetime
from typing import List, Optional, __all__

import prisma.enums
from prisma.models import Function, ObjectField, ObjectType
from pydantic import BaseModel, Field

from codex.api_model import ObjectTypeModel, Pagination
from codex.common.database import INCLUDE_FIELD, INCLUDE_TYPE
from codex.common.types import (
    extract_field_type,
    get_related_types,
    is_type_equal,
    normalize_type,
)


class FunctionDef(BaseModel):
    name: str
    arg_types: List[tuple[str, str]]
    arg_descs: dict[str, str]
    return_type: str | None = None
    return_desc: str
    is_implemented: bool
    function_desc: str
    function_code: str
    function_template: str | None = None

    def __generate_function_template(f) -> str:
        args_str = ", ".join([f"{name}: {type}" for name, type in f.arg_types])
        arg_desc = f"\n{' '*4}".join(
            [
                f'{name} ({type}): {f.arg_descs.get(name, "-")}'
                for name, type in f.arg_types
            ]
        )

        def_str = "async def" if "await " in f.function_code else "def"
        ret_type_str = f" -> {f.return_type}" if f.return_type else ""
        func_desc = f.function_desc.replace("\n", "\n    ")

        template = f"""
{def_str} {f.name}({args_str}){ret_type_str}:
    \"\"\"
    {func_desc}

    Args:
    {arg_desc}

    Returns:
    {f.return_type}{': ' + f.return_desc if f.return_desc else ''}
    \"\"\"
    pass
"""
        return "\n".join([line for line in template.split("\n")]).strip()

    def __init__(self, function_template: Optional[str] = None, **data):
        super().__init__(**data)
        self.function_template = (
            function_template or self.__generate_function_template()
        )

    def validate_matching_function(self, existing_func: Function):
        expected_args = [(f.name, f.typeName) for f in existing_func.FunctionArgs or []]
        expected_rets = (
            existing_func.FunctionReturn.typeName
            if existing_func.FunctionReturn
            else None
        )
        func_name = existing_func.functionName
        errors = []

        if any(
            [
                x[0] != y[0] or not is_type_equal(x[1], y[1]) and x[1] != "object"
                # TODO: remove sorted and provide a stable order for one-to-many arg-types.
                for x, y in zip(sorted(expected_args), sorted(self.arg_types))
            ]
        ):
            errors.append(
                f"Function {func_name} has different arguments than expected, expected {expected_args} but got {self.arg_types}"
            )
        if (
            not is_type_equal(expected_rets, self.return_type)
            and expected_rets != "object"
        ):
            errors.append(
                f"Function {func_name} has different return type than expected, expected {expected_rets} but got {self.return_type}"
            )

        if errors:
            raise Exception("Signature validation errors:\n  " + "\n  ".join(errors))


PYTHON_TYPES = set(__all__)


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

    if object.Fields is None:
        print(f"Fields is None and should be an array. \n {object}")
        raise AssertionError(f"Fields is None and should be an array. \n {object}")
    fields = object.Fields

    field_inputs = []
    for field in fields:
        for related_type in field.related_types or []:
            if related_type.name in available_objects:
                continue
            available_objects = await create_object_type(
                related_type, available_objects
            )

        field.type = normalize_type(field.type)
        if field.value is None and field.type.startswith("Optional"):
            field.value = "None"

        field_inputs.append(
            {
                "name": field.name,
                "description": field.description,
                "typeName": field.type,
                "value": field.value,
                "RelatedTypes": {
                    "connect": [
                        {"id": t.id}
                        for t in get_related_types(field.type, available_objects)
                    ]
                },
            }
        )

    typing_imports = []
    if object.is_pydantic:
        typing_imports.append("from pydantic import BaseModel")
    if object.is_enum:
        typing_imports.append("from enum import Enum")

    created_object_type = await ObjectType.prisma().create(
        data={
            "name": object.name,
            "code": object.code,
            "description": object.description,
            "Fields": {"create": field_inputs},
            "importStatements": typing_imports,
            "isPydantic": object.is_pydantic,
            "isEnum": object.is_enum,
        },
        **INCLUDE_FIELD,  # type: ignore
    )
    available_objects[object.name] = created_object_type

    # Connect the fields of available objects to the newly created object.
    # Naively check each available object if it has a related field to the new object.
    # TODO(majdyz): Optimize this step if needed.
    for obj in available_objects.values():
        if obj.Fields is None:
            raise AssertionError("Fields should be an array")

        for field in obj.Fields:
            if object.name not in extract_field_type(field.typeName):
                continue

            if field.RelatedTypes is None:
                raise AssertionError("RelatedTypes should be an array")

            if object.name in [f.name for f in field.RelatedTypes]:
                continue

            # Link created_object_type.id to the field.RelatedTypes
            reltypes = get_related_types(field.typeName, available_objects)
            updated_object_field = await ObjectField.prisma().update(
                where={"id": field.id},
                data={"RelatedTypes": {"connect": [{"id": t.id} for t in reltypes]}},
                **INCLUDE_TYPE,  # type: ignore
            )
            if updated_object_field:
                field.RelatedTypes = updated_object_field.RelatedTypes

    return available_objects


class ResumePoint(BaseModel):
    id: str | None = None
    name: str
    updatedAt: datetime.datetime
    userId: str | None = None
    applicationId: str | None = None
    interviewId: str | None = None
    specificationId: str | None = None
    completedAppId: str | None = None
    deploymentId: str | None = None


class ResumePointsList(BaseModel):
    resume_points: List[ResumePoint]
    pagination: Pagination


class APIRouteSpec(BaseModel):
    """
    A Software Module for the application
    """

    module_name: str
    http_verb: prisma.enums.HTTPVerb
    function_name: str
    path: str
    description: str
    access_level: prisma.enums.AccessLevel
    allowed_access_roles: list[str]
    request_model: ObjectTypeModel
    response_model: ObjectTypeModel


class FunctionSpec(BaseModel):
    name: str
    description: str
    func_args: Optional[ObjectTypeModel] = Field(
        description="The Function args", default=None
    )
    return_type: Optional[ObjectTypeModel] = Field(
        description="The Function return tyep", default=None
    )
