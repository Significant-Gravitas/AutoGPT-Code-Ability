import logging
from typing import List

from prisma.models import CodeGraph as CodeGraphDBModel
from prisma.models import CompiledRoute, CompletedApp
from prisma.models import FunctionDefinition as FunctionDefDBModel
from prisma.models import Specification

from codex.api_model import Indentifiers
from codex.developer.write_function import WriteFunctionAIBlock

logger = logging.getLogger(__name__)


async def develop_application(
    ids: Indentifiers, code_graphs: List[CodeGraphDBModel], spec: Specification
) -> CompletedApp:
    """
    Develop the application
    """
    completed_graphs = await write_code_graphs(ids, code_graphs, spec)
    if not completed_graphs:
        raise ValueError("No code graphs found")

    app = await CompletedApp.prisma().create(
        data={
            "compiledRoutes": {"connect": [{"id": c.id} for c in completed_graphs]},
            "spec": {"connect": {"id": spec.id}},
            "name": spec.name,
            "description": spec.context,
        }
    )
    return app


async def write_code_graphs(
    ids: Indentifiers,
    code_graphs: List[CodeGraphDBModel],
    spec: Specification,
) -> List[CompiledRoute]:
    completed_graphs = []
    for code_graph in code_graphs:
        cg = await CodeGraphDBModel.prisma().find_unique(
            where={"id": code_graph.id},
            include={"functionDefs": True, "routeSpec": True},
        )
        if not cg:
            raise ValueError(f"CodeGraph {code_graph.id} not found")

        if not cg.routeSpec:
            raise ValueError(f"No route spec found for code graph {cg.id}")

        written_functions = await code_functions(ids, cg)

        funciton_ids = [{"id": f.id} for f in written_functions]
        croute = await CompiledRoute.prisma().create(
            data={
                "codeGraph": {"connect": {"id": cg.id}},
                "code": cg.code_graph,
                "description": cg.routeSpec.description,
                "functions": {"connect": funciton_ids},
                "apiRouteSpec": {"connect": {"id": code_graph.routeSpecId}},
            }
        )

        completed_graphs.append(croute)
    return completed_graphs


async def code_functions(
    ids: Indentifiers, code_graph: CodeGraphDBModel
) -> List[FunctionDefDBModel]:
    """
    Code the functions in the code graph
    """
    if not code_graph.functionDefs:
        raise ValueError(f"No function defs found for code graph {code_graph.id}")

    functions = []
    for i, function_def in enumerate(code_graph.functionDefs):
        logger.info(
            f"{i+1}/{len(code_graph.functionDefs)}  Coding function {function_def.name}"
        )
        function_obj = await create_code(ids, code_graph.function_name, function_def)
        functions.append(function_obj)

    return functions


async def create_code(
    ids: Indentifiers, appilcation_context: str, function_def: FunctionDefDBModel
) -> str:
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
