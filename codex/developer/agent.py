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
    app = await CompletedApp.prisma().create(
        data={
            "compiledRoutes": {"connect": [{"id": c.id for c in completed_graphs}]},
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

        writen_functions = await code_functions(ids, cg)

        croute = await CompiledRoute.prisma().create(
            data={
                "codeGraph": {"connect": {"id": cg.id}},
                "code": cg.code_graph,
                "description": cg.routeSpec.description,
                "functions": {"connect": [{"id": f.id for f in writen_functions}]},
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
    functions = []
    for function_def in code_graph.functionDefs:
        logger.info(f"Coding function {function_def.name}")
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
