import logging
from .model import ApplicationRequirements


logger = logging.getLogger(__name__)


def define_requirements(task: str) -> ApplicationRequirements:
    """
    Takes a task and defines the requirements for the task

    Relevant chains:

    codex/chains/decompose_task.py

    TODO: Work out the interface for this
    """
    pass


def hardcoded_requirements(task: str) -> ApplicationRequirements:
    """

    This will take the application name and return the manualy
    defined requirements for the application in the correct format
    """
    logger.warning("⚠️ Using hardcoded requirements")
    pass
