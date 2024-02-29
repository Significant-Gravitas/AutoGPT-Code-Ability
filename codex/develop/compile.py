import ast
import logging
from typing import List, Set

from prisma.models import (
    APIRouteSpec,
    CompiledRoute,
    CompletedApp,
    Function,
    ObjectField,
    ObjectType,
    Package,
    Specification,
)
from prisma.types import CompiledRouteCreateInput, CompletedAppCreateInput
from pydantic import BaseModel
from sqlalchemy import func

from codex.api_model import Identifiers

logger = logging.getLogger(__name__)


class CompiledFunction(BaseModel):
    packages: List[Package]
    imports: List[str]
    code: str
    pydantic_models: List[str] = []


async def compile_route(
    ids: Identifiers, route_root_func: Function, api_route: APIRouteSpec
) -> CompiledRoute:
    """
    Compiles a route by generating a CompiledRoute object.

    Args:
        ids (Identifiers): The identifiers used in the route.
        route_root_func (Function): The root function of the route.
        api_route (APIRouteSpec): The specification of the API route.

    Returns:
        CompiledRoute: The compiled route object.

    """
    compiled_function = await recursive_compile_route(route_root_func)

    unique_packages = list(set([package.id for package in compiled_function.packages]))
    compiled_function.imports.append("from pydantic import BaseModel")
    code = "\n".join(compiled_function.imports)
    code += "\n\n"
    code += "\n\n".join(compiled_function.pydantic_models)
    code += "\n\n"
    code += compiled_function.code
    data = CompiledRouteCreateInput(
        description=api_route.description,
        Packages={"connect": [{"id": package_id} for package_id in unique_packages]},
        fileName=api_route.functionName + "_service.py",
        mainFunctionName=route_root_func.functionName,
        compiledCode=code,
        RootFunction={"connect": {"id": route_root_func.id}},
        ApiRouteSpec={"connect": {"id": api_route.id}},
    )
    compiled_route = await CompiledRoute.prisma().create(data)
    return compiled_route


async def recursive_compile_route(
    in_function: Function, object_type_ids: Set[str] = set()
) -> CompiledFunction:
    """
    Recursively compiles a function and its child functions
    into a single CompiledFunction object.

    Args:
        ids (Identifiers): The identifiers for the function.
        function (Function): The function to compile.

    Returns:
        CompiledFunction: The compiled function.

    Raises:
        ValueError: If the function code is missing.
    """
    # Can't see how to do recursive lookup with prisma, so I'm checking the next
    # layer down each time. This is a bit of a hack, can be improved later.
    function = await Function.prisma().find_unique_or_raise(
        where={"id": in_function.id},
        include={
            "ParentFunction": True,
            "ChildFunction": {"include": {"ApiRouteSpec": True}},
        },
    )
    logger.info(f"Compiling function: {function.id}")

    pydantic_models = []
    new_object_types = set()
    if function.FunctionArgs is not None:
        for arg in function.FunctionArgs:
            pydantic_models.append(process_object_field(arg, new_object_types))

    if function.FunctionReturn is not None:
        pydantic_models.append(
            process_object_field(function.FunctionReturn, new_object_types)
        )

    if function.ChildFunction is None:
        packages = []
        if function.Packages:
            packages = function.Packages
        if function.functionCode is None:
            raise ValueError(f"Leaf Function code is required! {function.id}")
        code = "\n".join(function.importStatements)
        code += "\n\n"
        code += function.functionCode

        try:
            tree = ast.parse(code)
        except Exception as e:
            raise ValueError(f"Syntax error in function code: {e}, {code}")

        return CompiledFunction(
            packages=packages,
            imports=function.importStatements,
            code=function.functionCode,
            pydantic_models=pydantic_models,
        )
    else:
        packages = []
        imports = []
        pydantic_models = []
        code = ""
        for child_function in function.ChildFunction:
            compiled_function = await recursive_compile_route(child_function)
            packages.extend(compiled_function.packages)
            imports.extend(compiled_function.imports)
            pydantic_models.extend(compiled_function.pydantic_models)
            code += "\n\n"
            code += compiled_function.code

        if function.Packages:
            packages.extend(function.Packages)
        imports.extend(function.importStatements)

        if function.functionCode is None:
            raise ValueError(f"Function code is required! {function.id}")

        code += "\n\n"
        code += function.functionCode
        check_code = "\n".join(imports)
        check_code += "\n\n"
        check_code += code

        try:
            tree = ast.parse(check_code)
        except Exception as e:
            raise ValueError(f"Syntax error in function code: {e}, {code}")

        return CompiledFunction(
            packages=packages,
            imports=imports,
            code=code,
            pydantic_models=pydantic_models,
        )


async def create_app(
    ids: Identifiers, spec: Specification, compiled_routes: List[CompiledRoute]
) -> CompletedApp:
    """
    Create an app using the given identifiers, specification, and compiled routes.

    Args:
        ids (Identifiers): The identifiers for the app.
        spec (Specification): The specification for the app.
        compiled_routes (List[CompiledRoute]): The compiled routes for the app.

    Returns:
        CompletedApp: The completed app object.
    """
    if spec.ApiRouteSpecs is None:
        raise ValueError("Specification must have at least one API route.")

    data = CompletedAppCreateInput(
        name=spec.name,
        description=spec.context,
        User={"connect": {"id": ids.user_id}},
        CompiledRoutes={"connect": [{"id": route.id} for route in compiled_routes]},
        Specification={"connect": {"id": spec.id}},
        Application={"connect": {"id": ids.app_id}},
    )
    app = await CompletedApp.prisma().create(data)
    return app


def process_object_type(obj: ObjectType, object_type_ids: Set[str] = set()) -> str:
    """
    Generate a Pydantic object based on the given ObjectType.

    Args:
        obj (ObjectType): The ObjectType to generate the Pydantic object for.

    Returns:
        str: The generated Pydantic object as a string.
    """
    if obj.Fields is None:
        raise ValueError(f"ObjectType {obj.name} has no fields.")

    template: str = ""
    sub_types: List[str] = []
    field_strings: List[str] = []
    for field in obj.Fields:
        if field.typeId is not None:
            sub_types.append(process_object_field(field, object_type_ids))

        field_strings.append(
            f"{' '*4}{field.name}: {field.typeName}  # {field.description}"
        )

    fields = "\n".join(
        [
            f"{' '*4}{field.name}: {field.typeName}  # {field.description}"
            for field in obj.Fields
        ]
    )

    fields: str = "\n".join(field_strings)
    # Returned as a string to preserve class declaration order
    template += "\n\n".join(sub_types)
    template += f"""

class {obj.name}(BaseModel):
    \"\"\"
    {obj.description}
    \"\"\"
{fields}
    """
    return template


def process_object_field(field: ObjectField, object_type_ids: Set[str]) -> str:
    """
    Process an object field and return the Pydantic classes
    generated from the field's type.

    Args:
        field (ObjectField): The object field to process.
        object_type_ids (Set[str]): A set of object type IDs that
                                    have already been processed.

    Returns:
        str: The Pydantic classes generated from the field's type.

    Raises:
        AssertionError: If the field type is None.
    """
    if field.typeId is None or field.typeId in object_type_ids:
        # If the field is a primitive type or we have already processed this object,
        # we don't need to do anything
        return ""

    assert field.Type is not None, "Field type is None"

    object_type_ids.add(field.typeId)

    pydantic_classes = process_object_type(field.Type, object_type_ids)

    return pydantic_classes
