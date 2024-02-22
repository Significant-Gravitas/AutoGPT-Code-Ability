import asyncio
import logging

from prisma.models import APIRouteSpec, Function, Specification
from prisma.types import FunctionCreateInput

from codex.api_model import Identifiers
from codex.develop.develop import DevelopAIBlock
from codex.develop.model import ApplicationGraphs, FunctionDef

logger = logging.getLogger(__name__)

# hacky way to list all generated functions, will be replaced with a vector-lookup
generated_function_defs: list[FunctionDef] = []


async def recursive_create_function(
    ids: Identifiers,
    route_description: str,
    func_name: str,
    func_template: str,
    api_route: APIRouteSpec,
) -> Function:
    if func_template and "  pass" not in func_template:
        # LLM is kind enough to implement the code, no need to do another AIblock.
        create_input = FunctionCreateInput(
            **{
                "functionName": func_name,
                "apiPath": api_route.path,
                "functionCode": func_template,
                "imports": [],
                "FunctionDefinitions": {"create": []},
                "ApiRouteSpec": {"connect": {"id": api_route.id}},
            }
        )
        return await Function.prisma().create(data=create_input)

    description = f"""
{func_template}

High-level Goal: {route_description}"""

    logger.info(f"Creating code graph for {func_name}")

    code_graph: Function = await DevelopAIBlock().invoke(
        ids=ids,
        invoke_params={
            "function_name": func_name,
            "api_route": api_route,
            "description": description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != func_name
            ],
        },
    )

    function_defs: list[FunctionDef] = []
    for child in await FunctionDefinition.prisma().find_many(
        where={"CodeGraph": {"id": code_graph.id}}
    ):
        child_func_def = FunctionDef(
            name=child.name,
            doc_string=child.docString,
            args=child.args,
            return_type=child.returnType,
            function_template=child.functionTemplate,
        )
        function_defs.append(child_func_def)

    # DFS to traverse all the child functions, and recursively generate code graphs
    generated_function_defs.extend(function_defs)
    for child_func_def in function_defs:
        child_graph = await recursive_create_function(
            ids,
            route_description,
            child_func_def.name,
            child_func_def.function_template,
            api_route,
        )
        await Function.prisma().update(
            where={"id": child_graph.id}, data={"parentFunctionId": code_graph.id}
        )

    return code_graph


async def create_code_graphs(
    ids: Identifiers, spec: Specification
) -> ApplicationGraphs:
    """
    Create the code graphs for given api routes in parallel
    """
    assert spec.ApiRouteSpecs, "No api routes found in the spec"

    async def create_graph(api_route):
        logger.info(f"Creating code graph for {api_route.path}")
        codegraph = DevelopAIBlock()
        return await codegraph.invoke(
            ids=ids,
            invoke_params={
                "function_name": api_route.functionName,
                "api_route": api_route,
                "description": api_route.description,
            },
        )

    tasks = [create_graph(api_route) for api_route in spec.ApiRouteSpecs]
    code_graphs = await asyncio.gather(*tasks)
    return ApplicationGraphs(code_graphs=code_graphs)
