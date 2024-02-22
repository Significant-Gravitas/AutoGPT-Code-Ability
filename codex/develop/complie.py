from typing import List

from prisma.models import (
    APIRouteSpec,
    CompiledRoute,
    CompletedApp,
    Function,
    Specification,
)

from codex.api_model import Identifiers


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
    return CompiledRoute(**{})


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
    return CompletedApp(**{})
    """
    return CompletedApp(**{})
