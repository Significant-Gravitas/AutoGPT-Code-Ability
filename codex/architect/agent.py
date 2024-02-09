import logging
from typing import List

from codex.architect.model import CodeGraph
from codex.requirements.model import ApplicationRequirements
from codex.architect.codegraph import CodeGraphAIBlock
from openai import OpenAI
from codex.api_model import Indentifiers

logger = logging.getLogger(__name__)



def create_code_graphs(ids: Indentifiers, requirements: ApplicationRequirements, oai_client: OpenAI) -> List[CodeGraph]:
    """
    Create the code graph for a given api route
    """
    code_graphs = []
    for api_route in requirements.api_routes:
        logger.info(f"Creating code graph for {api_route.path}")
        codegraph = CodeGraphAIBlock(
            oai_client=oai_client,
        )

        cg = codegraph.invoke(
            ids=ids,
            invoke_params={
                "function_name": api_route.function_name,
                "api_route": api_route,
                "description": api_route.description,
            }
        )
        code_graphs.append(cg)
    return code_graphs
