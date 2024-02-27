import asyncio
import logging
import os

from prisma.enums import FunctionState
from prisma.models import APIRouteSpec, CompletedApp, Function, Specification

from codex.api_model import Identifiers
from codex.develop.compile import compile_route, create_app
from codex.develop.develop import DevelopAIBlock

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
    compiled_routes = []
    if spec.ApiRouteSpecs:
        for api_route in spec.ApiRouteSpecs:
            route_root_func = await develop_route(
                [], ids, api_route, api_route.description, api_route.functionName
            )
            logger.info(f"Route function id: {route_root_func.id}")
            compiled_route = await compile_route(ids, route_root_func, api_route)
            compiled_routes.append(compiled_route)

    return await create_app(ids, spec, compiled_routes)


async def develop_route(
    generated_functions: list[
        Function
    ],  # TODO: remove this, replace with vector-lookup.
    ids: Identifiers,
    api_route: APIRouteSpec,
    goal_description: str,
    function_name: str,
    function_id: str = None,
    function_template: str = None,
    depth: int = 0,
) -> Function:
    """
    Recursively develops a function and its child functions
    based on the provided function definition and api route spec.

    Args:
        generated_functions (list[Function]): The list of already generated functions, used to promote function re-use.
        ids (Identifiers): The identifiers for the function.
        api_route (APIRouteSpec): The API route specification.
        goal_description (str): The high-level goal of the function to create.
        function_name (str): The name of the function to create.
        function_id (str): The id of the function to create. If not provided, a new root-function will be created.
        function_template (str): The docstring/template of the function to create.
        depth (int): The depth of the recursion.

    Returns:
        Function: The developed route function.
    """
    logger.info(
        f"Developing for route: {api_route.path} - Func: {function_name}, depth: {depth}"
    )
    if depth >= RECURSION_DEPTH_LIMIT:
        raise ValueError("Recursion depth exceeded")

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": function_name,
            "goal": goal_description,
            "function_signature": function_template,
            "provided_functions": [
                f.template
                for f in generated_functions
                if f.functionName != function_name and f.parentFunctionId
            ],
            # api_route is not used by the prompt, but is used by the function
            "api_route": api_route,
            # function_id is used, so we can update the function with the implementation
            "function_id": function_id,
            "allow_stub": depth < RECURSION_DEPTH_LIMIT,
        },
    )

    if route_function.ChildFunction:
        generated_functions.extend(route_function.ChildFunction)
        logger.info(f"\tDeveloping {len(route_function.ChildFunction)} child functions")
        tasks = [
            develop_route(
                ids=ids,
                goal_description=goal_description,
                function_id=child.id,
                function_name=child.functionName,
                function_template=child.template,
                api_route=api_route,
                depth=depth + 1,
                generated_functions=generated_functions,
            )
            for child in route_function.ChildFunction
            if child.state == FunctionState.DEFINITION
        ]
        await asyncio.gather(*tasks)
    else:
        logger.info(f"❌ No child functions to develop")
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
