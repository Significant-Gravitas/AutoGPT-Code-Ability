import logging

from .model import (
    APIRouteRequirement,
    ApplicationRequirements,
    Parameter,
    RequestModel,
    ResponseModel,
)

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
    if task == "Availability Checker":
        # Request Model for availability check
        check_availability_request = RequestModel(
            name="CheckAvailabilityRequest",
            description="A request to check the availability status of a professional based on the current time and their schedule.",
            params=[
                Parameter(
                    name="current_time",
                    param_type="datetime",
                    description="The timestamp at which the availability status is being requested.",
                ),
                Parameter(
                    name="schedule_data",
                    param_type="List[Tuple[datetime, datetime]]",
                    description="A list of tuples representing the schedule of the professional, where each tuple contains start and end times of appointments or busy periods.",
                ),
            ],
        )

        # Response Model for availability status
        availability_status_response = ResponseModel(
            name="AvailabilityStatusResponse",
            description="A response indicating the current availability status of the professional.",
            params=[
                Parameter(
                    name="availability_status",
                    param_type="str",
                    description="The current availability status of the professional. Possible values are 'Available' and 'Busy'.",
                )
            ],
        )

        return ApplicationRequirements(
            name="Availability Checker",
            context="Function that returns the availability of professionals, updating based on current activity or schedule.",
            api_routes=[
                APIRouteRequirement(
                    method="POST",
                    path="/availability",
                    description="Function that returns the availability of professionals, updating based on current activity or schedule.",
                    request_model=check_availability_request,
                    response_model=availability_status_response,
                    database_schema=None,
                ),
            ],
        )
    else:
        raise NotImplementedError(f"Task {task} not implemented")
