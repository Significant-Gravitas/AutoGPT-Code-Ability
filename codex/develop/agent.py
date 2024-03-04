import asyncio
import logging
import os

from prisma.enums import FunctionState
from prisma.models import (
    APIRouteSpec,
    CompletedApp,
    Function,
    ObjectField,
    ObjectType,
    Specification,
)

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
    compiled_routes = []
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
            generated_objects = [
                v for v in [api_route.RequestObject, api_route.ResponseObject] if v
            ]
            model = construct_function(function_def, generated_objects)
            function = await Function.prisma().create(
                data=model,
                include={"FunctionArgs": True, "FunctionReturn": True},
            )

            route_root_func = await develop_route(
                generated_objects=generated_objects,
                generated_functions=[],
                ids=ids,
                api_route=api_route,
                goal_description=spec.context,
                function=function,
            )
            logger.info(f"Route function id: {route_root_func.id}")
            compiled_route = await compile_route(ids, route_root_func, api_route)
            compiled_routes.append(compiled_route)

    return await create_app(ids, spec, compiled_routes)


async def develop_route(
    generated_objects: list[ObjectType],
    generated_functions: list[Function],
    ids: Identifiers,
    api_route: APIRouteSpec,
    goal_description: str,
    function: Function,
    depth: int = 0,
) -> Function:
    """
    Recursively develops a function and its child functions
    based on the provided function definition and api route spec.

    Args:
        generated_objects (list[ObjectType]): The list of already generated objects, used to promote object re-use.
        generated_functions (list[Function]): The list of already generated functions,
                                              used to promote function re-use.
        ids (Identifiers): The identifiers for the function.
        api_route (APIRouteSpec): The API route specification.
        goal_description (str): The high-level goal of the function to create.
        function (Function): The function to develop.
        depth (int): The depth of the recursion.

    Returns:
        Function: The developed route function.
    """
    logger.info(
        f"Developing for route: {api_route.path} - Func: {function.functionName}, depth: {depth}"
    )
    if depth >= RECURSION_DEPTH_LIMIT:
        raise ValueError("Recursion depth exceeded")

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": function.functionName,
            "goal": goal_description,
            "function_signature": function.template,
            # function_args is not used by the prompt, but is used by the function validation
            "function_args": [(f.name, f.typeName) for f in function.FunctionArgs],
            # function_rets is not used by the prompt, but is used by the function validation
            "function_rets": function.FunctionReturn.typeName
            if function.FunctionReturn
            else None,
            "provided_functions": [
                f.template
                for f in generated_functions
                if f.functionName != function.functionName and f.parentFunctionId
            ]
            + [generate_object_template(obj) for obj in generated_objects],
            # api_route is not used by the prompt, but is used by the function
            "api_route": api_route,
            "available_objects": generated_objects,
            # function_id is used, so we can update the function with the implementation
            "function_id": function.id,
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
                function=child,
                api_route=api_route,
                depth=depth + 1,
                generated_functions=generated_functions,
                generated_objects=generated_objects,
            )
            for child in route_function.ChildFunction
            if child.state == FunctionState.DEFINITION
        ]
        await asyncio.gather(*tasks)
    else:
        logger.info(f"📦 No child functions to develop")
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
