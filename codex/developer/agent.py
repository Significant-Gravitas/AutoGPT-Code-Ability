import asyncio
import logging
from typing import List

from prisma.models import CodeGraph as CodeGraphDBModel
from prisma.models import CompiledRoute, CompletedApp
from prisma.models import FunctionDefinition as FunctionDefDBModel
from prisma.models import Specification

from codex.api_model import Identifiers
from codex.developer.write_function import WriteFunctionAIBlock

logger = logging.getLogger(__name__)


async def develop_application(
    ids: Identifiers, code_graphs: List[CodeGraphDBModel], spec: Specification
) -> CompletedApp:
    """
    Develop the application
    """
    completed_graphs = await write_code_graphs(ids, code_graphs, spec)
    if not completed_graphs:
        raise ValueError("No code graphs found")

    app = await CompletedApp.prisma().create(
        data={
            "CompiledRoutes": {"connect": [{"id": c.id} for c in completed_graphs]},
            "Specification": {"connect": {"id": spec.id}},
            "name": spec.name,
            "description": spec.context,
        }
    )
    return app


async def write_code_graphs(
    ids: Identifiers,
    code_graphs: List[CodeGraphDBModel],
    spec: Specification,
) -> List[CompiledRoute]:
    completed_graphs = []
    for code_graph in code_graphs:
        cg = await CodeGraphDBModel.prisma().find_unique(
            where={"id": code_graph.id},
            include={"FunctionDefinitions": True, "APIRouteSpec": True},
        )
        if not cg:
            raise ValueError(f"CodeGraph {code_graph.id} not found")

        if not cg.APIRouteSpec:
            raise ValueError(f"No route spec found for code graph {cg.id}")

        written_functions = await code_functions(ids, cg)

        funciton_ids = [{"id": f.id} for f in written_functions]
        croute = await CompiledRoute.prisma().create(
            data={
                "CodeGraph": {"connect": {"id": cg.id}},
                "code": cg.code_graph,
                "description": cg.routeSpec.description,
                "Functions": {"connect": funciton_ids},
                "ApiRouteSpec": {"connect": {"id": code_graph.apiRouteSpecId}},
            }
        )

        completed_graphs.append(croute)
    return completed_graphs


async def code_functions(
    ids: Identifiers, code_graph: CodeGraphDBModel
) -> List[FunctionDefDBModel]:
    """
    Code the functions in the code graph in parallel.
    """
    if not code_graph.FunctionDefinitions:
        raise ValueError(f"No function defs found for code graph {code_graph.id}")

    # Define a local async function that wraps the create_code call
    async def code_function(function_def):
        logger.info(f"Coding function {function_def.name}")
        return await create_code(ids, code_graph.function_name, function_def)

    # Create a list of coroutine objects for each function definition
    tasks = [code_function(function_def) for function_def in code_graph.functionDefs]

    # Run all the coroutine objects concurrently and collect their results
    functions = await asyncio.gather(*tasks)

    return functions


async def create_code(
    ids: Identifiers, appilcation_context: str, function_def: FunctionDefDBModel
) -> FunctionDefDBModel:
    """
    Gets the coding agent to write or lookup the code for a function
    """
    # TODO: Add code lookup
    aiblock = WriteFunctionAIBlock()
    ids.function_def_id = function_def.id
    code = await aiblock.invoke(
        ids=ids,
        invoke_params={
            "function_def": function_def,
            "application_context": appilcation_context,
            "function_template": function_def.function_template,
        },
    )
    return code
