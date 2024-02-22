import asyncio
import logging

from openai import AsyncOpenAI
from prisma.models import APIRouteSpec, CodeGraph, FunctionDefinition, Specification
from prisma.types import CodeGraphCreateInput

from codex.api_model import Identifiers
from codex.architect.codegraph import CodeGraphAIBlock
from codex.architect.model import ApplicationGraphs, FunctionDef

logger = logging.getLogger(__name__)

# hacky way to list all generated functions, will be replaced with a vector-lookup
generated_function_defs: list[FunctionDef] = []


async def recursive_create_code_graphs(
    ids: Identifiers,
    goal: str,
    func_def: FunctionDef,
    api_route: APIRouteSpec,
    oai_client: AsyncOpenAI = AsyncOpenAI(),
) -> CodeGraph:
    # They are kind enough to implement the code, no need to do another AIblock.
    if func_def.function_template and "  pass" not in func_def.function_template:
        create_input = CodeGraphCreateInput(
            **{
                "functionName": func_def.name,
                "apiPath": api_route.path,
                "codeGraph": func_def.function_template,
                "imports": [],
                "FunctionDefinitions": {"create": []},
                "ApiRouteSpec": {"connect": {"id": api_route.id}},
            }
        )
        return await CodeGraph.prisma().create(data=create_input)

    description = f"""
{func_def.function_template}

High-level Goal: {goal}"""

    logger.info(f"Creating code graph for {func_def.name}")

    code_graph: CodeGraph = await CodeGraphAIBlock(oai_client=oai_client).invoke(
        ids=ids,
        invoke_params={
            "function_name": func_def.name,
            "api_route": api_route,
            "description": description,
            "provided_functions": [
                f.function_template
                for f in generated_function_defs
                if f.name != func_def.name
            ],
        },
    )

    # query FunctionDefinitions for the current code_graph
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

    generated_function_defs.extend(function_defs)
    for child_func_def in function_defs:
        child_graph = await recursive_create_code_graphs(
            ids, goal, child_func_def, api_route, oai_client
        )
        await CodeGraph.prisma().update(
            where={"id": child_graph.id}, data={"parentCodeGraphId": code_graph.id}
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
        codegraph = CodeGraphAIBlock()
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
