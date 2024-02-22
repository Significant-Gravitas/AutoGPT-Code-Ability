import asyncio
import logging
import re

from prisma.models import APIRouteSpec, Function, Specification
from prisma.types import FunctionCreateInput

from codex.api_model import Identifiers
from codex.develop.develop import DevelopAIBlock
from codex.develop.model import FunctionDef

logger = logging.getLogger(__name__)

# hacky way to list all generated functions, will be replaced with a vector-lookup
generated_function_defs: list[FunctionDef] = []


async def develop_route(
    ids: Identifiers,
    route_description: str,
    func_name: str,
    func_template: str,
    api_route: APIRouteSpec,
) -> Function:
    global generated_function_defs
    generated_function_defs = []

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": func_name,
            "api_route": api_route,
            "description": route_description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != func_name
            ],
        },
    )

    if route_function.ChildFunction:
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

    description = f"""
{function_def.template}

High-level Goal: {route_description}"""

    route_function: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": function_def.functionName,
            "api_route": api_route,
            "description": description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != function_def.functionName
            ],
        },
    )

    if route_function.ChildFunction:
        for child in route_function.ChildFunction:
            # We don't need to store the output here,
            # as the function will be stored in the database
            await recursive_create_function(ids, route_description, child, api_route)

    return route_function
