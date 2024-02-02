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
    match task:
        case "Availability Checker":
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
        case "Invoice Generator":
            invoice_model = RequestModel(
                name="invoicemodel",
                description="An object used to generte an invoice",
                params=[
                    Parameter(
                        name="services_rendered",
                        param_type="array",
                        description="a list of the services being rendered broken down by hours, service_description, and items used for the service. Items used is further broken down by name, description, unit_cost, and units used",
                    ),
                    Parameter(
                        name="tax_rate",
                        param_type="float",
                        description="local tax rate used for calculations",
                    ),
                ],
            )

            invoice_response = ResponseModel(
                name="inoviceresponse",
                description="A pdf of an invoice",
                params=[
                    Parameter(
                        name="availability_status",
                        param_type="file",
                        description="A PDF file for the invoice",
                    )
                ],
            )

            return ApplicationRequirements(
                name="Invoice Generator",
                context="The Dynamic Invoice Generator is a backend function designed to create detailed invoices for professional services. This function will process input data regarding services rendered, billable hours, parts used, and applicable rates or taxes, to generate a comprehensive invoice. This function operates without the need for database access, relying solely on the input provided at the time of invoice creation.",
                api_routes=[
                    APIRouteRequirement(
                        method="POST",
                        path="/create_invoice",
                        description="Function that returns the availability of professionals, updating based on current activity or schedule.",
                        request_model=invoice_model,
                        response_model=invoice_response,
                        database_schema=None,
                    ),
                ],
            )
        case 'Appointment Optimization Tool':
            appointment_model = RequestModel(
                name="AppointmentModel",
                description="An object used to make good times for an appointment",
                params=[
                    Parameter(
                        name="availablility_calendar",
                        param_type="datetime[]",
                        description="A data structure (like a list or array) containing the professional's available time slots for a given period (e.g., a week). Each time slot should include the start and end times.",
                    ),
                    Parameter(
                        name="prefered_hours",
                        param_type="str",
                        description="The professional's preferred working hours (e.g., 9 AM to 5 PM), which could be a default setting or specified for each day.",
                    ), Parameter(
                        name="travel_time_buffer",
                        param_type="time",
                        description="Information regarding the time needed to travel between appointments. This could be a fixed duration or vary based on the time of day or location.",
                    ), Parameter(
                        name="time_frame",
                        param_type="str",
                        description="The time frame during which the client wishes to schedule the appointment (e.g., a specific date or range of dates).",
                    ),
                ],
            )

            appointment_response = ResponseModel(
                name="AppointmentResponse",
                description="A few good times for appointments",
                params=[
                    Parameter(
                        name="slots",
                        param_type="datetime[]",
                        description="A list of optimal appointment slots, each with a start and end time. This list should be sorted by preference or efficiency.",
                    ),
                    Parameter(
                        name="alternatives",
                        param_type="datetime[]",
                        description="If no optimal slots are available, provide a list of alternative slots, clearly indicating that they are outside the preferred criteria.",
                    )
                ],
            )

            return ApplicationRequirements(
                name="Appointment Scheduler",
                context="The function for suggesting optimal appointment slots is designed to provide professionals and clients with the best possible meeting times based on the professional's availability, preferred working hours, and travel time considerations. This function operates in real-time, relying on input data without needing access to a database.",
                api_routes=[
                    APIRouteRequirement(
                        method="POST",
                        path="/create_invoice",
                        description="Function that returns the availability of professionals, updating based on current activity or schedule.",
                        request_model=appointment_model,
                        response_model=appointment_response,
                        database_schema=None,
                    ),
                ],
            )
        case 'Distance Calculator':
            distance_model = RequestModel(
                name="DistanceInput",
                description="An object used to find the start and end locations",
                params=[
                    Parameter(
                        name="start_location",
                        param_type="Tuple[float, float]",
                        description="AThe current location of the professional, provided as latitude and longitude coordinates.",
                    ),
                    Parameter(
                        name="end_location",
                        param_type="Tuple[str,str]",
                        description="TThe location where the client wishes to have the appointment, provided as latitude and longitude coordinates.",
                    ),
                ],
            )

            distance_response = ResponseModel(
                name="DistanceOutput",
                description="Output of calcuating the distance",
                params=[
                    Parameter(
                        name="distance",
                        param_type="Tuple[float, float]",
                        description="The calculated distance between the two locations, preferably in both kilometers and miles.",
                    ),
                    Parameter(
                        name="travel_time",
                        param_type="time",
                        description="An estimation of the time it would take for the professional to travel from their location to the client's location, considering average travel conditions.",
                    )
                ],
            )

            return ApplicationRequirements(
                name="Distance Calculator",
                context="The Distance Calculator is a tool that calculates the distance between the professional's and the client's locations to aid in planning travel time for appointments.",
                api_routes=[
                    APIRouteRequirement(
                        method="POST",
                        path="/calculate_distance",
                        description="Function that returns the distance for travel time based upon input",
                        request_model=distance_model,
                        response_model=distance_response,
                        database_schema=None,
                    ),
                ],
            )

        case _:
            raise NotImplementedError(f"Task {task} not implemented")
