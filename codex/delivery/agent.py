import logging
from typing import List

from codex.architect.model import CodeGraph

logger = logging.getLogger(__name__)


def complie_code_graphs(code_graphs: List[CodeGraph]) -> List[str]:
    """
    Packages the app for delivery

    NOTE: This agent will hopefull not reqire llm calls

    TODO: Work out the interface for this
    """
    pass
