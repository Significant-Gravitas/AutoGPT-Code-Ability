import ast
import logging
import re
from datetime import datetime
from typing import List, Set

import black
import isort
from prisma.models import (
    CompiledRoute,
    CompletedApp,
    Function,
    ObjectField,
    ObjectType,
    Package,
    Specification,
)
from prisma.types import CompiledRouteUpdateInput, CompletedAppCreateInput
from pydantic import BaseModel

import codex.common.model
from codex.api_model import Identifiers
from codex.common.database import INCLUDE_FIELD, INCLUDE_FUNC
from codex.deploy.model import Application
from codex.develop.function import generate_object_template

logger = logging.getLogger(__name__)


class CompiledFunction(BaseModel):
    packages: List[Package]
    imports: List[str]
    code: str
    pydantic_models: List[str] = []


class ComplicationFailure(Exception):
    pass


async def compile_route(
    compiled_route_id: str, route_root_func: Function
) -> CompiledRoute:
    """
    Compiles a route by generating a CompiledRoute object.

    Args:
        compiled_route_id (str): The ID of the compiled route.
        route_root_func (Function): The root function of the route.
    Returns:
        CompiledRoute: The compiled route object.
    """
    compiled_function = await recursive_compile_route(route_root_func, set())

    unique_packages = list(set([package.id for package in compiled_function.packages]))
    code = "\n".join(compiled_function.imports)
    code += "\n\n"
    code += "\n\n".join(compiled_function.pydantic_models)
    code += "\n\n"
    code += compiled_function.code

    # Run the formatting engines
    formatted_code = code
    try:
        formatted_code = isort.code(formatted_code)
        formatted_code = black.format_str(formatted_code, mode=black.FileMode())
    except Exception as e:
        # We move on with unformatted code if there's an error
        logger.exception(f"Error formatting code: {e} for route #{compiled_route_id}")

    data = CompiledRouteUpdateInput(
        Packages={"connect": [{"id": package_id} for package_id in unique_packages]},
        compiledCode=formatted_code,
    )
    compiled_route = await CompiledRoute.prisma().update(
        where={"id": compiled_route_id}, data=data
    )
    if compiled_route is None:
        raise ComplicationFailure(
            f"Failed to update compiled route {compiled_route_id}"
        )
    return compiled_route


def add_full_import_parth_to_custom_types(module_name: str, arg: ObjectField) -> str:
    """
    Adds the full import path to custom types in the given argument.

    Args:
        module_name (str): The name of the module.
        arg (ObjectField): The argument to process.

    Returns:
        str: The modified argument type with the full import path.

    """
    if not arg.RelatedTypes:
        return arg.typeName

    ret_type = arg.typeName
    logger.debug(f"Arg name: {arg.name}, arg type: {arg.typeName}")

    # For each related type, replace the type name with the full import path
    renamed_types: dict[str, str] = {}

    for t in arg.RelatedTypes:
        if t.isPydantic or t.isEnum:
            renamed_types[t.name] = f"{module_name}.{t.name}"

    ret_type = codex.common.model.normalize_type(ret_type, renamed_types)

    return ret_type


async def recursive_compile_route(
    in_function: Function, object_type_ids: Set[str]
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
            **INCLUDE_FUNC["include"],
            "ParentFunction": INCLUDE_FUNC,
            "ChildFunctions": INCLUDE_FUNC,
        },  # type: ignore
    )
    logger.info(f"⚙️ Compiling function: {function.functionName}")

    if function.functionCode is None:
        raise ValueError(f"Function code is required! {function.functionName}")

    packages = []
    imports = []
    code = []
    model = []

    if function.FunctionArgs is not None:
        for arg in function.FunctionArgs:
            obj_types = await get_object_field_deps(arg, object_type_ids)
            model.extend([generate_object_template(obj_type) for obj_type in obj_types])
            for obj in obj_types:
                imports.extend(obj.importStatements)

    if function.FunctionReturn is not None:
        obj_types = await get_object_field_deps(
            function.FunctionReturn, object_type_ids
        )
        model.extend([generate_object_template(obj_type) for obj_type in obj_types])
        for obj in obj_types:
            imports.extend(obj.importStatements)

    # Child Functions
    if function.ChildFunctions is None:
        raise AssertionError("ChildFunctions should be an array")
    for child_function in function.ChildFunctions:
        compiled_function = await recursive_compile_route(
            child_function, object_type_ids
        )
        packages.extend(compiled_function.packages)
        imports.extend(compiled_function.imports)
        model.extend(compiled_function.pydantic_models)
        code.append(compiled_function.code)

    # Package
    if function.Packages:
        packages.extend(function.Packages)

    # Imports
    imports.extend(function.importStatements)
    imports = sorted(set(imports))

    # Code
    code.append(function.functionCode)

    # Check Code
    try:
        check_code = "\n".join(imports)
        check_code += "\n\n" + "\n\n".join(model)
        check_code += "\n\n" + "\n\n".join(code)
        ast.parse(check_code)
    except Exception as e:
        raise ValueError(f"Syntax error in function code: {e}, {code}")

    return CompiledFunction(
        packages=packages,
        imports=imports,
        code="\n\n".join(code),
        pydantic_models=model,
    )


async def get_object_type_deps(
    obj_type_id: str, object_type_ids: Set[str]
) -> List[ObjectType]:
    # Lookup the object getting all its subfields
    obj = await ObjectType.prisma().find_unique_or_raise(
        where={"id": obj_type_id},
        **INCLUDE_FIELD,  # type: ignore
    )
    if obj.Fields is None:
        raise ValueError(f"ObjectType {obj.name} has no fields.")

    objects: List[ObjectType] = []
    for field in obj.Fields:
        if field.RelatedTypes:
            objects.extend(await get_object_field_deps(field, object_type_ids))

    return objects + [obj]


async def get_object_field_deps(
    field: ObjectField, object_type_ids: Set[str]
) -> List[ObjectType]:
    """
    Process an object field and return the Pydantic classes
    generated from the field's type.

    Args:
        field (ObjectField): The object field to process.
        object_type_ids (Set[str]): A set of object type IDs that
                                    have already been processed.

    Returns:
        List[ObjectType]: The object types generated from the field's type.

    Raises:
        AssertionError: If the field type is None.
    """
    # Lookup the field object getting all its subfields
    field = await ObjectField.prisma().find_unique_or_raise(
        where={"id": field.id},
        include={"RelatedTypes": True},
    )

    if field.RelatedTypes is None:
        raise AssertionError("Field RelatedTypes should be an array")
    types = [t for t in field.RelatedTypes if t.id not in object_type_ids]

    if not types:
        # If the field is a primitive type or we have already processed this object,
        # we don't need to do anything
        logger.debug(
            f"Skipping field {field.name} as it's a primitive type or already processed"
        )
        return []

    logger.debug(f"Processing field {field.name} of type {field.typeName}")
    object_type_ids.update([t.id for t in types])

    # TODO: this can run in parallel
    pydantic_classes = []
    for type in types:
        pydantic_classes.extend(await get_object_type_deps(type.id, object_type_ids))

    return pydantic_classes


def create_server_route_code(compiled_route: CompiledRoute) -> str:
    """
    Create the server route code for a compiled route.

    Args:
        compiled_route (CompiledRoute): The compiled route to create the
                                        server route code for.

    Returns:
        str: The server route code.
    """
    main_function = compiled_route.RootFunction

    if main_function is None:
        raise ValueError("Compiled route must have a root function.")

    return_type = main_function.FunctionReturn
    if return_type is None:
        raise AssertionError("Compiled route must have a return type.")

    args = main_function.FunctionArgs
    if args is None:
        raise AssertionError("Compiled route must have function arguments.")

    route_spec = compiled_route.ApiRouteSpec
    if route_spec is None:
        raise AssertionError("Compiled route must have an API route spec.")

    module_name = f"project.{compiled_route.fileName.replace('.py', '')}"

    is_file_response = False
    response_model = "Response"
    route_response_annotation = "Response"
    if (
        return_type.RelatedTypes
        and return_type.RelatedTypes[0]
        and return_type.RelatedTypes[0].Fields
        and return_type.RelatedTypes[0].Fields[0].typeName == "bytes"
    ):
        is_file_response = True
    else:
        if return_type.typeName is not None:
            response_model = f"{module_name}.{return_type.typeName} | Response"
            route_response_annotation = return_type.typeName

    # 4. Determine path parameters
    path_params = extract_path_params(route_spec.path)

    func_args_names = set([arg.name for arg in args])
    if not set(path_params).issubset(func_args_names):
        logger.warning(
            f"Path parameters {path_params} not in function arguments {func_args_names}"
        )

    http_verb = str(route_spec.method)
    route_decorator = f"@app.{http_verb.lower()}('{route_spec.path}'"
    if not is_file_response:
        route_decorator += f", response_model={module_name}.{route_response_annotation}"

    route_decorator += ")\n"

    # TODO(SwiftyOS): consider replacing the prefix with a proper import and func call.
    route_function_def = (
        f"async def api_{http_verb.lower()}_{main_function.functionName}("
    )
    route_function_def += ", ".join(
        [
            f"{arg.name}: {add_full_import_parth_to_custom_types(module_name, arg)}"
            for arg in args
        ]
    )
    route_function_def += ")"

    return_response = ""
    if is_file_response:
        route_function_def += " -> StreamingResponse:"
        headers = """
        headers = {
        "Content-Disposition": f"attachment; filename={res.file_name}"
    }
        """
        return_response = f"""
        {headers}
        return StreamingResponse(
            content=res.data,
            media_type=res.media_type,
            headers=headers)
    """
    else:
        route_function_def += f" -> {response_model}:"
        return_response = "return res"

    function_body = f"""
    \"\"\"
    {route_spec.description}
    \"\"\"
    try:
        res = await {module_name}.{main_function.functionName}({", ".join([arg.name for arg in args])})
        {return_response}
    except Exception as e:
        logger.exception("Error processing request")
        res = dict()
        res["error"] =  str(e)
        return Response(
            content=jsonable_encoder(res),
            status_code=500,
            media_type="application/json",
        )
    """
    route_code = route_decorator
    route_code += route_function_def
    route_code += function_body
    route_code += "\n\n"

    try:
        ast.parse(route_code)
    except Exception as e:
        raise ComplicationFailure(f"Syntax error in route code: {e}, {route_code}")

    return route_code


def extract_path_params(path: str) -> List[str]:
    """
    Extracts path parameters from a given path.

    Args:
        path (str): The path string containing path parameters.

    Returns:
        List[str]: A list of path parameters extracted from the path.
    """
    matches = re.findall(r"\{(.*?)\}", path)
    return matches


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

    if not ids.user_id:
        raise ValueError("User ID is required.")

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


def create_server_code(completed_app: CompletedApp) -> Application:
    """
    Args:
        application (Application): _description_

    Returns:
        Application: _description_
    """
    name = completed_app.name
    desc = completed_app.description

    server_code_imports = [
        "from fastapi import FastAPI",
        "from fastapi.responses import Response, StreamingResponse",
        "from fastapi.encoders import jsonable_encoder",
        "from prisma import Prisma",
        "from contextlib import asynccontextmanager",
        "import logging",
        "import prisma",
        "import io",
        "from typing import *",
    ]
    server_code_header = f"""logger = logging.getLogger(__name__)

db_client = Prisma(auto_register=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_client.connect()
    yield
    await db_client.disconnect()

app = FastAPI(title="{name}", lifespan=lifespan, description='''{desc}''')

"""

    service_routes_code = []
    if completed_app.CompiledRoutes is None:
        raise ValueError("Application must have at least one compiled route.")

    packages = [
        Package(
            packageName="fastapi",
            specifier="",
            version="",
            id="fastapi",
            createdAt=datetime.now(),
        ),
        Package(
            packageName="pydantic",
            specifier="",
            version="",
            id="pydantic",
            createdAt=datetime.now(),
        ),
        Package(
            packageName="uvicorn",
            specifier="",
            version="",
            id="uvicorn",
            createdAt=datetime.now(),
        ),
        Package(
            packageName="prisma",
            specifier="",
            version="",
            id="prisma",
            createdAt=datetime.now(),
        ),
    ]
    for i, compiled_route in enumerate(completed_app.CompiledRoutes):
        if compiled_route.ApiRouteSpec is None:
            raise ValueError(f"Compiled route {compiled_route.id} has no APIRouteSpec")

        if compiled_route.Packages:
            packages.extend(compiled_route.Packages)

        if compiled_route.RootFunction is None:
            raise ValueError(f"Compiled route {compiled_route.id} has no root function")

        server_code_imports.append(
            f"import project.{compiled_route.fileName.replace('.py', '')}"
        )

        service_routes_code.append(create_server_route_code(compiled_route))

    # Compile the server code
    server_code = "\n".join(server_code_imports)
    server_code += "\n\n"
    server_code += server_code_header
    server_code += "\n\n"
    server_code += "\n\n".join(service_routes_code)

    # Update the application with the server code
    sorted_content = isort.code(server_code)
    formatted_code = black.format_str(sorted_content, mode=black.FileMode())

    return Application(
        name=name,
        description=desc,
        server_code=formatted_code,
        completed_app=completed_app,
        packages=packages,
    )
