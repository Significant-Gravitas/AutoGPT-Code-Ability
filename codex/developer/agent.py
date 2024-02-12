import logging
from typing import List

from codex.architect.model import CodeGraph, FunctionDef
from codex.developer.model import Function

logger = logging.getLogger(__name__)


def write_code_graphs(code_graphs: List[CodeGraph]) -> List[CodeGraph]:
    completed_graphs = []
    for code_graph in code_graphs:
        completed_cg = code_functions(code_graph)
        completed_graphs.append(completed_cg)
    return completed_graphs


def code_functions(code_graph: CodeGraph) -> CodeGraph:
    """
    Code the functions in the code graph
    """
    code_graph.functions = {}
    for function_name, function_def in code_graph.function_defs.items():
        logger.info(f"Coding function {function_name}")
        packages, function_code = create_code(code_graph.function_name, function_def)
        code_graph.functions[function_name] = Function(
            name=function_name,
            doc_string=function_def.doc_string,
            args=function_def.args,
            return_type=function_def.return_type,
            code=function_code,
            packages=packages,
        )
    return code_graph


def create_code(appilcation_context: str, function_def: FunctionDef) -> str:
    """
    Gets the coding agent to write or lookup the code for a function
    """
    # TODO: Add code lookup
    # function = write_code_chain(
    #     invoke_params={
    #         "node": function_def,
    #         "application_context": appilcation_context,
    #         "function_template": function_def.function_template,
    #     }
    # )
    # TODO: Add function storage
    # return function
    pass
