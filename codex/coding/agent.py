import logging
from typing import List

from codex.architect.model import CodeGraph, FunctionDef
from codex.chains.write_node import write_code_chain

logger = logging.getLogger(__name__)


def write_code_graphs(code_graphs: List[CodeGraph]):
    completed_graphs = []
    for code_graph in code_graphs:
        completed_cg = code_functions(code_graph)
        completed_graphs.append(completed_cg)
    return completed_graphs


def code_functions(code_graph: CodeGraph) -> CodeGraph:
    """
    Code the functions in the code graph
    """
    functions = []
    for function_name, function_def in code_graph.function_defs.items():
        logger.info(f"Coding function {function_name}")
        function = create_code(code_graph.name, function_def)
        functions.append(function)
    code_graph.functions = functions
    return code_graph


def create_code(appilcation_context: str, function_def: FunctionDef) -> str:
    """
    Gets the coding agent to write or lookup the code for a function
    """
    # TODO: Add code lookup
    function = write_code_chain(
        invoke_params={
            "node": function_def,
            "application_context": appilcation_context,
            "function_template": function_def.template,
        }
    )
    # TODO: Add function storage
    return function
