import logging

from openai import OpenAI
from prisma.models import Specification

from codex.api_model import Indentifiers
from codex.architect.codegraph import CodeGraphAIBlock
from codex.architect.model import ApplicationGraphs

logger = logging.getLogger(__name__)


async def create_code_graphs(
    ids: Indentifiers, spec: Specification, oai_client: OpenAI = OpenAI()
) -> ApplicationGraphs:
    """
    Create the code graph for a given api route
    """
    code_graphs = []
    for api_route in spec.apiRoutes:
        logger.info(f"Creating code graph for {api_route.path}")
        codegraph = CodeGraphAIBlock(
            oai_client=oai_client,
        )

        cg = await codegraph.invoke(
            ids=ids,
            invoke_params={
                "function_name": api_route.functionName,
                "api_route": api_route,
                "description": api_route.description,
            },
        )
        code_graphs.append(cg)
    return ApplicationGraphs(code_graphs=code_graphs)


if __name__ == "__main__":
    import codex.requirements.hardcoded

    spec = codex.requirements.hardcoded.availability_checker_requirements()
    ids = Indentifiers(user_id=1, app_id=1)
    create_code_graphs(ids, spec)
