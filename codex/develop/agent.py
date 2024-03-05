import asyncio
import logging
import os

from prisma.enums import FunctionState
from prisma.models import (
    CompiledRoute,
    CompletedApp,
    Function,
    Specification,
)
from prisma.types import CompiledRouteCreateInput, CompletedAppCreateInput

from codex.api_model import Identifiers
from codex.develop.compile import compile_route, create_app
from codex.develop.develop import DevelopAIBlock
from codex.develop.function import construct_function, generate_object_template
from codex.develop.model import FunctionDef

RECURSION_DEPTH_LIMIT = int(os.environ.get("RECURSION_DEPTH_LIMIT", 3))

logger = logging.getLogger(__name__)


async def develop_application(ids: Identifiers, spec: Specification) -> CompletedApp:
    """
    Develops an application based on the given identifiers and specification.

    Args:
        ids (Identifiers): The identifiers used for development.
        spec (Specification): The specification of the application.

    Returns:
        CompletedApp: The completed application.

    """
    app = await create_app(ids, spec, [])

    if spec.ApiRouteSpecs:
        for api_route in spec.ApiRouteSpecs:
            if not api_route.RequestObject:
                types = []
                descs = {}
            elif api_route.RequestObject.Fields:
                # Unwrap the first level of the fields if it's a nested object.
                types = [(f.name, f.typeName) for f in api_route.RequestObject.Fields]
                descs = {f.name: f.description for f in api_route.RequestObject.Fields}
            else:
                types = [("request", api_route.RequestObject.name)]
                descs = {"request": api_route.RequestObject.description}

            function_def = FunctionDef(
                name=api_route.functionName,
                arg_types=types,
                arg_descs=descs,
                return_type=api_route.ResponseObject.name
                if api_route.ResponseObject
                else None,
                return_desc=api_route.ResponseObject.description
                if api_route.ResponseObject
                else None,
                is_implemented=False,
                function_desc=api_route.description,
                function_code="",
            )
            available_types = {
                obj.name: obj
                for obj in [api_route.RequestObject, api_route.ResponseObject]
                if obj
            }
            compiled_route = await CompiledRoute.prisma().create(
                data=CompiledRouteCreateInput(
                    description=api_route.description,
                    fileName=api_route.functionName + "_service.py",
                    mainFunctionName=api_route.functionName,
                    compiledCode="",  # This will be updated by compile_route
                    RootFunction={
                        "create": construct_function(function_def, available_types)
                    },
                    CompletedApp={"connect": {"id": app.id}},
                    ApiRouteSpec={"connect": {"id": api_route.id}},
                ),
                include={
                    "RootFunction": {
                        "include": {"FunctionArgs": True, "FunctionReturn": True}
                    }
                },
            )

            route_root_func = await develop_route(
                ids=ids,
                compiled_route_id=compiled_route.id,
                goal_description=spec.context,
                function=compiled_route.RootFunction,
            )
            logger.info(f"Route function id: {route_root_func.id}")
            await compile_route(compiled_route.id, route_root_func, api_route)

    return app


async def develop_route(
    ids: Identifiers,
    compiled_route_id: str,
    goal_description: str,
    function: Function,
    depth: int = 0,
) -> Function:
    """
    Recursively develops a function and its child functions
    based on the provided function definition and api route spec.

    Args:
        ids (Identifiers): The identifiers for the function.
        compiled_route_id (int): The id for which CompiledRoute the function is being developed.
        goal_description (str): The high-level goal of the function to create.
        function (Function): The function to develop.
        depth (int): The depth of the recursion.

    Returns:
        Function: The developed route function.
    """
    logger.info(
        f"Developing for compiled route: "
        f"{compiled_route_id} - Func: {function.functionName}, depth: {depth}"
    )
    if depth >= RECURSION_DEPTH_LIMIT:
        raise ValueError("Recursion depth exceeded")

    compiled_route = await CompiledRoute.prisma().find_unique_or_raise(
        where={"id": compiled_route_id},
        include={
            "Functions": {"include": {"FunctionArgs": True, "FunctionReturn": True}}
        },
    )
    generated_func = {}
    generated_objs = {}
    for func in compiled_route.Functions:
        if func.functionName != function.functionName:
            generated_func[func.functionName] = func
        for arg in func.FunctionArgs:
            generated_objs[arg.typeName] = arg
        if func.FunctionReturn:
            generated_objs[func.FunctionReturn.typeName] = func.FunctionReturn

    route_function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": function.functionName,
            "goal": goal_description,
            "function_signature": function.template,
            # function_args is not used by the prompt, but used for function validation
            "function_args": [(f.name, f.typeName) for f in function.FunctionArgs],
            # function_rets is not used by the prompt, but used for function validation
            "function_rets": function.FunctionReturn.typeName
            if function.FunctionReturn
            else None,
            "provided_functions": [func.template for func in generated_func.values()]
            + [generate_object_template(f) for f in generated_objs.values()],
            # compiled_route_id is not used by the prompt, but is used by the function
            "compiled_route_id": compiled_route_id,
            # available_objects is not used by the prompt, but is used by the function
            "available_objects": generated_objs,
            # function_id is used, so we can update the function with the implementation
            "function_id": function.id,
            "allow_stub": depth < RECURSION_DEPTH_LIMIT,
        },
    )

    if route_function.ChildFunctions:
        logger.info(
            f"\tDeveloping {len(route_function.ChildFunctions)} child functions"
        )
        tasks = [
            develop_route(
                ids=ids,
                goal_description=goal_description,
                function=child,
                api_route=api_route,
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
    import asyncio

    import prisma
    from prisma.models import APIRouteSpec

    import codex.common.test_const as test_consts
    from codex.common.ai_model import OpenAIChatClient
    from codex.common.logging import setup_logging
    from codex.requirements.database import get_latest_specification

    OpenAIChatClient.configure({})
    setup_logging(local=True)
    client = prisma.Prisma(auto_register=True)

    async def run_me():
        await client.connect()
        ids = test_consts.identifier_1
        spec = await get_latest_specification(ids.user_id, ids.app_id)
        ans = await develop_application(ids=ids, spec=spec)
        await client.disconnect()
        return ans

    ans = asyncio.run(run_me())
    logger.info(ans)
