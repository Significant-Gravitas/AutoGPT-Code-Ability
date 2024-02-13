import logging
from typing import List

from prisma.models import (
    CodeGraph as CodeGraphDBModel,
    FunctionDefinition as FunctionDefDBModel,
    CompiledRoute,
    CompletedApp,
    Specification
)
from codex.developer.model import Function
from codex.developer.write_function import WriteFunctionAIBlock
from codex.api_model import Indentifiers

logger = logging.getLogger(__name__)


async def develop_application(
    code_graphs: List[CodeGraphDBModel], spec: Specification
) -> CompletedApp:
    """
    Develop the application
    """
    completed_graphs = await write_code_graphs(code_graphs, spec)
    app = await CompletedApp.prisma().create(
        data={
            "compiled_routes": {"connect": [{"id": c.id for c in completed_graphs}]},
            "application": {"connect": {"id": spec.app.id}},
            "spec": {"connect": {"id": spec.id}},
            "name": spec.name,
            "description": spec.context,
        }
    )
    return app

async def write_code_graphs(
    code_graphs: List[CodeGraphDBModel],
    spec: Specification,
) -> List[CompiledRoute]:
    completed_graphs = []
    for code_graph in code_graphs:
        writen_functions = code_functions(code_graph)

        croute = await CompiledRoute.prisma().create(
            data={
                "code_graph": {"connect": {"id": code_graph.id}},
                "code": code_graph.code,
                "description": code_graph.description,
                "functions": {"connect": [{"id": f.id for f in writen_functions}]},
            }
        )

        completed_graphs.append(croute)
    return completed_graphs


async def code_functions(code_graph: CodeGraphDBModel) -> List[FunctionDefDBModel]:
    """
    Code the functions in the code graph
    """
    code_graph.functions = {}
    functions = []
    for function_name, function_def in code_graph.function_defs.items():
        logger.info(f"Coding function {function_name}")
        function_obj = create_code(code_graph.function_name, function_def)
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
