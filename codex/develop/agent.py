import logging
import os
from re import T

from prisma.models import APIRouteSpec, CompletedApp, Function, Specification

from codex.api_model import Identifiers
from codex.develop.compile import compile_route, create_app
from codex.develop.develop import DevelopAIBlock
from codex.develop.model import FunctionDef

RECURSION_DEPTH_LIMIT = int(os.environ.get("RECURSION_DEPTH_LIMIT", 3))

logger = logging.getLogger(__name__)

# hacky way to list all generated functions, will be replaced with a vector-lookup
generated_function_defs: list[FunctionDef] = []


async def develop_application(ids: Identifiers, spec: Specification) -> CompletedApp:
    """
    Develops an application based on the given identifiers and specification.

    Args:
        ids (Identifiers): The identifiers used for development.
        spec (Specification): The specification of the application.

    Returns:
        CompletedApp: The completed application.

    """
    compiled_routes = []
    if spec.ApiRouteSpecs:
        for api_route in spec.ApiRouteSpecs:
            route_root_func = await develop_route(
                ids, api_route.description, api_route.functionName, api_route
            )
            compiled_route = await compile_route(ids, route_root_func, api_route)
            compiled_routes.append(compiled_route)

    return await create_app(ids, spec, compiled_routes)


async def develop_route(
    ids: Identifiers,
    route_description: str,
    func_name: str,
    api_route: APIRouteSpec,
) -> Function:
    """
    Develops a route based on the given parameters.

    Args:
        ids (Identifiers): The identifiers for the route function.
        route_description (str): The description of the route function.
        func_name (str): The name of the route function.
        api_route (APIRouteSpec): The API route specification.

    Returns:
        Function: The developed route function.
    """
    global generated_function_defs
    generated_function_defs = []
    logger.info(f"Developing route: {route_description}")

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": func_name,
            "description": route_description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != func_name
            ],
            # api_route is not used by the prompt, but is used by the function
            "api_route": api_route,
        },
    )
    if route_function.ChildFunction:
        logger.info(f"\tDeveloping {len(route_function.ChildFunction)} child functions")
        for child in route_function.ChildFunction:
            # We don't need to store the output here,
            # as the function will be stored in the database
            await recursive_create_function(ids, route_description, child, api_route)

    return route_function


async def recursive_create_function(
    ids: Identifiers,
    route_description: str,
    function_def: Function,
    api_route: APIRouteSpec,
    depth: int = 0,
) -> Function:
    """
    Recursively creates a function and its child functions
    based on the provided function definition.

    Args:
        ids (Identifiers): The identifiers for the function.
        route_description (str): The description of the route.
        function_def (Function): The function definition.
        api_route (APIRouteSpec): The API route specification.

    Returns:
        Function: The created function.
    """
    if depth > 0:
        logger.warning(f"Recursion depth: {depth} for route {route_description}")
    if depth > RECURSION_DEPTH_LIMIT:
        raise ValueError("Recursion depth exceeded")

    description = f"""
{function_def.template}

High-level Goal: {route_description}"""

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": function_def.functionName,
            "description": description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != function_def.functionName
            ],
            # api_route is not used by the prompt, but is used by the function
            "api_route": api_route,
            # function_id is used so we can update the function with the implementation
            "function_id": function_def.id,
        },
    )

    if route_function.ChildFunction:
        for child in route_function.ChildFunction:
            # We don't need to store the output here,
            # as the function will be stored in the database
            await recursive_create_function(
                ids, route_description, child, api_route, depth + 1
            )

    return route_function


if __name__ == "__main__":
    import asyncio
    import prisma
    import codex.common.test_const as test_consts
    from prisma.models import APIRouteSpec
    from codex.requirements.database import get_latest_specification
    from codex.common.logging import setup_logging
    from codex.common.ai_model import OpenAIChatClient

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
