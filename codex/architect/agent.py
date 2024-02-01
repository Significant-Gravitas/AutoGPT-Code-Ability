import logging

from codex.requirements.model import ApplicationRequirements
from codex.chains.code_graph import write_graph_chain

logger = logging.getLogger(__name__)


def create_code_graph(requirements: ApplicationRequirements):
    """
    Create the code graph for a given api route
    """
    for api_route in requirements.api_routes:
        logger.info(f"Creating code graph for {api_route.path}")

        cg = write_graph_chain(
            {
                "function_name": api_route.path.replace("/", ""),
                "description": f"### **Overview**\n{requirements.context}\n\n"
                f"### **API Route**\n{str(api_route)}",
            }
        )
        return cg
