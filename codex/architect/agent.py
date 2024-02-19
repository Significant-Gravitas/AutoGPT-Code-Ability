import asyncio
import logging

from openai import AsyncOpenAI
from prisma.models import Specification

from codex.api_model import Indentifiers
from codex.architect.codegraph import CodeGraphAIBlock
from codex.architect.model import ApplicationGraphs

logger = logging.getLogger(__name__)


async def create_code_graphs(
    ids: Indentifiers, spec: Specification, oai_client: AsyncOpenAI = AsyncOpenAI()
) -> ApplicationGraphs:
    """
    Create the code graphs for given api routes in parallel
    """
    assert spec.apiRoutes, "No api routes found in the spec"

    async def create_graph(api_route):
        logger.info(f"Creating code graph for {api_route.path}")
        codegraph = CodeGraphAIBlock(oai_client=oai_client)
        return await codegraph.invoke(
            ids=ids,
            invoke_params={
                "function_name": api_route.functionName,
                "api_route": api_route,
                "description": api_route.description,
            },
        )

    tasks = [create_graph(api_route) for api_route in spec.apiRoutes]
    code_graphs = await asyncio.gather(*tasks)
    return ApplicationGraphs(code_graphs=code_graphs)
