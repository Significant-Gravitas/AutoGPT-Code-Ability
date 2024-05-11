import asyncio
import logging
import os

import prisma
import prisma.enums
from langsmith import traceable
from prisma.enums import FunctionState
from prisma.models import (
    Application,
    CompiledRoute,
    CompletedApp,
    Function,
    ObjectType,
    Specification,
)
from prisma.types import CompiledRouteCreateInput

import codex
import codex.common
import codex.common.database
from codex.api_model import Identifiers
from codex.common.ai_block import LLMFailure
from codex.common.database import INCLUDE_FUNC
from codex.common.model import APIRouteSpec, FunctionDef, FunctionSpec
from codex.database import create_completed_app
from codex.develop.compile import (
    compile_route,
    get_object_field_deps,
    get_object_type_deps,
)
from codex.develop.database import get_compiled_route, get_deliverable
from codex.develop.develop import DevelopAIBlock, NiceGUIDevelopAIBlock
from codex.develop.function import construct_function, generate_object_template
from codex.requirements.blocks.ai_page_decompose import PageDecompositionBlock
from codex.requirements.database import create_single_function_spec, get_specification

RECURSION_DEPTH_LIMIT = int(os.environ.get("RECURSION_DEPTH_LIMIT", 2))

logger = logging.getLogger(__name__)


@traceable
async def write_function(
    ids: Identifiers, app: Application, function_spec: FunctionSpec
) -> CompiledRoute:
    api_route_spec = APIRouteSpec(
        module_name="Solo Function",
        http_verb=prisma.enums.HTTPVerb.POST,
        function_name=function_spec.name,
        path="/",
        description=function_spec.description,
        access_level=prisma.enums.AccessLevel.PUBLIC,
        allowed_access_roles=[],
        request_model=function_spec.func_args,
        response_model=function_spec.return_type,
    )

    spec: Specification = await create_single_function_spec(ids, app, api_route_spec)

    completed_app = await create_completed_app(ids, spec)

    if not spec.Modules:
        raise ValueError("No modules found in the specification.")
    if not spec.Modules[0].ApiRouteSpecs:
        raise ValueError(
            "No API routes found in the first module of the specification."
        )

    return await process_api_route(
        api_route=spec.Modules[0].ApiRouteSpecs[0],
        ids=ids,
        spec=spec,
        completed_app=completed_app,
        lang="python",
    )


@traceable
async def process_api_route(
    api_route: prisma.models.APIRouteSpec,
    ids: Identifiers,
    spec: prisma.models.Specification,
    completed_app: prisma.models.CompletedApp,
    extra_functions: list[Function] = [],
    lang: str = "python",
) -> CompiledRoute:
    if not api_route.RequestObject:
        types = []
        descs = {}
    elif api_route.RequestObject.Fields:
        # Unwrap the first level of the fields if it's a nested object.
        types = [(f.name, f.typeName) for f in api_route.RequestObject.Fields]
        descs = {f.name: f.description or "" for f in api_route.RequestObject.Fields}
    else:
        types = [("request", api_route.RequestObject.name)]
        descs = {"request": api_route.RequestObject.description or ""}

    if not api_route.ResponseObject:
        ret_type = None
        ret_desc = ""
    else:
        ret_type = api_route.ResponseObject.name
        ret_desc = api_route.ResponseObject.description or ""

    function_def = FunctionDef(
        name=api_route.functionName,
        arg_types=types,
        arg_descs=descs,
        return_type=ret_type,
        return_desc=ret_desc,
        is_implemented=False,
        function_desc=api_route.description,
        function_code="",
    )
    object_type_ids = set()
    available_types = {
        dep_type.name: dep_type
        for obj in [api_route.RequestObject, api_route.ResponseObject]
        if obj
        for dep_type in await get_object_type_deps(obj.id, object_type_ids)
    }
    if api_route.RequestObject and api_route.RequestObject.Fields:
        # RequestObject is unwrapped, so remove it from the available types
        available_types.pop(api_route.RequestObject.name, None)

    file_name = (
        api_route.functionName + "_service.py"
        if lang == "python"
        else "ui_" + api_route.functionName + ".py"
    )

    compiled_route = await CompiledRoute.prisma().create(
        data=CompiledRouteCreateInput(
            description=api_route.description,
            fileName=file_name,
            mainFunctionName=api_route.functionName,
            compiledCode="",  # This will be updated by compile_route
            RootFunction={
                "create": await construct_function(function_def, available_types)
            },
            CompletedApp={"connect": {"id": completed_app.id}},
            ApiRouteSpec={"connect": {"id": api_route.id}},
        ),
        include={"RootFunction": INCLUDE_FUNC},  # type: ignore
    )
    if not compiled_route.RootFunction:
        raise ValueError("Root function not created")

    # Set all the ids for logging
    ids.spec_id = spec.id
    ids.compiled_route_id = compiled_route.id
    ids.function_id = compiled_route.RootFunction.id

    route_root_func = await develop_route(
        ids=ids,
        goal_description=completed_app.description or "",
        function=compiled_route.RootFunction,
        spec=spec,
        lang=lang,
        extra_functions=extra_functions,
    )
    logger.info(f"Route function id: {route_root_func.id}")
    available_funcs, available_objs = await populate_available_functions_objects(
        extra_functions
    )
    return await compile_route(
        compiled_route.id, route_root_func, spec, available_funcs, available_objs
    )


@traceable
async def develop_user_interface(ids: Identifiers) -> CompletedApp:
    if not ids.user_id or not ids.app_id or not ids.completed_app_id:
        raise ValueError("user_id, app_id, and completed_app_id are required")

    completed_app = await get_deliverable(ids.completed_app_id)
    available_functions = [
        route.RootFunction
        for route in completed_app.CompiledRoutes or []
        if route.RootFunction
    ]
    ids.spec_id = completed_app.specificationId

    functions_code = []
    for func in available_functions:
        if func.FunctionReturn and func.FunctionReturn.RelatedTypes:
            functions_code += [
                generate_object_template(t) for t in func.FunctionReturn.RelatedTypes
            ]

        if func.FunctionArgs:
            functions_code += [
                generate_object_template(t)
                for arg in func.FunctionArgs
                for t in arg.RelatedTypes or []
            ]

        functions_code.append(func.template)

    ai_block = PageDecompositionBlock()
    frontend_spec = await ai_block.invoke(
        ids=ids,
        invoke_params={
            "available_functions": {f.functionName: f for f in available_functions},
            "functions_code": functions_code,
        },
    )

    # Connect db table from the existing spec to the new spec
    if completed_app.specificationId:
        backend_spec = await get_specification(
            ids.user_id, ids.app_id, completed_app.specificationId
        )
        frontend_spec.DatabaseSchema = backend_spec.DatabaseSchema

    return await develop_application(ids, frontend_spec, lang="nicegui")


@traceable
async def develop_application(
    ids: Identifiers,
    spec: Specification,
    lang: str = "python",
    eat_errors: bool = True,
) -> CompletedApp:
    """
    Develops an application based on the given identifiers and specification.

    Args:
        ids (Identifiers): The identifiers used for development.
        spec (Specification): The specification of the application.

    Returns:
        CompletedApp: The completed application.

    """
    completed_app = await create_completed_app(ids, spec)

    # If the completed app is defined, use the functions from the provided completed app as already implemented functions.
    # This flow is used for developing the user interface.
    if ids.completed_app_id:
        existing_completed_app = await get_deliverable(ids.completed_app_id)
        extra_functions = [
            route.RootFunction
            for route in existing_completed_app.CompiledRoutes or []
            if route.RootFunction
        ]

    else:
        extra_functions = []

    tasks = []

    if spec.Modules:
        api_routes = []
        for module in spec.Modules:
            if module.ApiRouteSpecs:
                api_routes.extend(module.ApiRouteSpecs)

        for api_route in api_routes:
            # Schedule each API route for processing
            task = process_api_route(
                api_route,
                ids,
                spec,
                completed_app,
                extra_functions,
                lang,
            )
            tasks.append(task)

        # Run the tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        if any(isinstance(r, Exception) for r in results):
            exceptions = [r for r in results if isinstance(r, Exception)]
            # if the only exceptions are LLMFailures, we can continue
            if eat_errors and all(isinstance(r, LLMFailure) for r in exceptions):
                logger.warning(
                    f"App Id: {ids.app_id} Eating Errors developing API routes: {exceptions}"
                )
                pass
            else:
                error_message = "".join(f"\n* {e}" for e in exceptions)
                raise LLMFailure(
                    f"App Id: {ids.app_id} Error developing API routes: \n{error_message}"
                )
        else:
            logger.info("🚀 All API routes developed successfully")

    return completed_app


@traceable
async def populate_available_functions_objects(
    functions: list[Function],
) -> tuple[dict[str, Function], dict[str, ObjectType]]:
    generated_func: dict[str, Function] = {}
    generated_objs: dict[str, ObjectType] = {}

    object_ids = set()
    for func in functions:
        generated_func[func.functionName] = func

        # Populate generated request objects from the LLM
        for arg in func.FunctionArgs or []:
            for type in await get_object_field_deps(arg, object_ids):
                generated_objs[type.name] = type

        # Populate generated response objects from the LLM
        if func.FunctionReturn:
            for type in await get_object_field_deps(func.FunctionReturn, object_ids):
                generated_objs[type.name] = type

    return generated_func, generated_objs


@traceable
async def develop_route(
    ids: Identifiers,
    goal_description: str,
    function: Function,
    spec: Specification,
    lang: str,
    extra_functions: list[Function] = [],
    depth: int = 0,
) -> Function:
    """
    Recursively develops a function and its child functions
    based on the provided function definition and api route spec.

    Args:
        ids (Identifiers): The identifiers for the function.
        goal_description (str): The high-level goal of the function to create.
        function (Function): The function to develop.
        depth (int): The depth of the recursion.

    Returns:
        Function: The developed route function.
    """
    logger.info(
        f"Developing for compiled route: "
        f"{ids.compiled_route_id} - Func: {function.functionName}, depth: {depth}"
    )
    if not ids.compiled_route_id:
        raise ValueError("ids.compiled_route_id is required for developing a function")

    # Set the function id for logging
    ids.function_id = function.id

    if depth > RECURSION_DEPTH_LIMIT:
        raise ValueError("Recursion depth exceeded")

    compiled_route = await get_compiled_route(ids.compiled_route_id)
    functions = []
    if compiled_route.Functions:
        functions += compiled_route.Functions
    if compiled_route.RootFunction:
        functions.append(compiled_route.RootFunction)
    if extra_functions:
        functions += extra_functions

    generated_func, generated_objs = await populate_available_functions_objects(
        functions
    )

    provided_functions = [
        func.template
        for func in list(generated_func.values()) + extra_functions
        if func.functionName != function.functionName
    ] + [generate_object_template(f) for f in generated_objs.values()]

    database_schema = codex.common.database.get_database_schema(spec)

    dev_invoke_params = {
        "route_path": compiled_route.ApiRouteSpec.path
        if compiled_route.ApiRouteSpec
        else "/",
        "database_schema": database_schema,
        "function_name": function.functionName,
        "goal": goal_description,
        "function_signature": function.template,
        # function_args is not used by the prompt, but used for function validation
        "function_args": [(f.name, f.typeName) for f in function.FunctionArgs or []],
        # function_rets is not used by the prompt, but used for function validation
        "function_rets": function.FunctionReturn.typeName
        if function.FunctionReturn
        else None,
        "provided_functions": provided_functions,
        # compiled_route_id is not used by the prompt, but is used by the function
        "compiled_route_id": ids.compiled_route_id,
        # available_objects is not used by the prompt, but is used by the function
        "available_objects": generated_objs,
        # function_id is used, so we can update the function with the implementation
        "function_id": function.id,
        "available_functions": generated_func,
        "allow_stub": depth < RECURSION_DEPTH_LIMIT,
    }

    if lang == "nicegui":
        ai_block = NiceGUIDevelopAIBlock()
    else:
        ai_block = DevelopAIBlock()

    route_function = await ai_block.invoke(ids=ids, invoke_params=dev_invoke_params)

    if route_function.ChildFunctions:
        logger.info(
            f"\tDeveloping {len(route_function.ChildFunctions)} child functions"
        )
        tasks = [
            develop_route(
                ids=ids,
                goal_description=goal_description,
                function=child,
                spec=spec,
                lang=lang,
                extra_functions=extra_functions,
                depth=depth + 1,
            )
            for child in route_function.ChildFunctions
            if child.state == FunctionState.DEFINITION
        ]
        await asyncio.gather(*tasks)
    else:
        logger.info("📦 No child functions to develop")
        logger.debug(route_function.rawCode)
    return route_function


if __name__ == "__main__":
    import prisma

    import codex.common.test_const as test_consts
    from codex.common.ai_model import OpenAIChatClient
    from codex.common.logging_config import setup_logging
    from codex.requirements.database import get_latest_specification

    OpenAIChatClient.configure({})
    setup_logging()
    client = prisma.Prisma(auto_register=True)

    async def run_me():
        await client.connect()
        ids = test_consts.identifier_1
        assert ids.user_id
        assert ids.app_id
        spec = await get_latest_specification(ids.user_id, ids.app_id)
        ans = await develop_application(ids=ids, spec=spec)
        await client.disconnect()
        return ans

    ans = asyncio.run(run_me())
    logger.info(ans)
