import logging
from typing import List

from codex.chains.code_graph import CodeGraph, write_graph_chain
from codex.requirements.model import ApplicationRequirements

logger = logging.getLogger(__name__)


def create_code_graphs(requirements: ApplicationRequirements) -> List[CodeGraph]:
    """
    Create the code graph for a given api route
    """
    code_graphs = []
    for api_route in requirements.api_routes:
        logger.info(f"Creating code graph for {api_route.path}")

        cg = write_graph_chain(
            {
                "function_name": api_route.path.replace("/", ""),
                "description": f"### **Overview**\n{requirements.context}\n\n"
                f"### **API Route**\n{str(api_route)}",
            }
        )
        code_graphs.append(cg)
    return code_graphs
