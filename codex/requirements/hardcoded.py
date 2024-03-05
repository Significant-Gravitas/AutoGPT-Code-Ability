import logging

from prisma.enums import AccessLevel

from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    DatabaseSchema,
    DatabaseTable,
    Parameter,
    RequestModel,
    ResponseModel,
)

logger = logging.getLogger(__name__)


def availability_checker_requirements() -> ApplicationRequirements:
    # Define request and response models here
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
                param_type="list[tuple[datetime, datetime]]",
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
                function_name="check_availability",
                access_level=AccessLevel.PUBLIC,
                description="Function that returns the availability of professionals, updating based on current activity or schedule. This function operates without the need for database access, relying solely on the input provided in the request",
                request_model=check_availability_request,
                response_model=availability_status_response,
                database_schema=None,
            ),
        ],
    )


# Function to define requirements for the Invoice Generator
def invoice_generator_requirements() -> ApplicationRequirements:
    # Define request and response models here
    invoice_model = RequestModel(
        name="InvoiceRequest",
        description="An object used to generte an invoice",
        params=[
            Parameter(
                name="services_rendered",
                param_type="list[tuple[float, str, list[tuple[str, str, float, float]]]]",
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
        name="InvoiceResponse",
        description="A pdf of an invoice",
        params=[
            Parameter(
                name="availability_status",
                param_type="bytes",
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
                function_name="create_invoice",
                access_level=AccessLevel.PUBLIC,
                description="This function will process input data regarding services rendered, billable hours, parts used, and applicable rates or taxes, to generate a comprehensive invoice as a pdf file. This function operates without the need for database access, relying solely on the input provided at the time of invoice creation.",
                request_model=invoice_model,
                response_model=invoice_response,
                database_schema=None,
            ),
        ],
    )


# Function to define requirements for the Appointment Optimization Tool
def appointment_optimization_requirements() -> ApplicationRequirements:
    # Define request and response models here
    appointment_model = RequestModel(
        name="AppointmentModel",
        description="An object used to make good times for an appointment",
        params=[
            Parameter(
                name="availability_calendar",
                param_type="list[datetime]",
                description="A data structure (like a list or array) containing the professional's available time slots for a given period (e.g., a week). Each time slot should include the start and end times.",
            ),
            Parameter(
                name="prefered_hours",
                param_type="str",
                description="The professional's preferred working hours (e.g., 9 AM to 5 PM), which could be a default setting or specified for each day.",
            ),
            Parameter(
                name="travel_time_buffer",
                param_type="time",
                description="Information regarding the time needed to travel between appointments. This could be a fixed duration or vary based on the time of day or location.",
            ),
            Parameter(
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
                param_type="list[datetime]",
                description="A list of optimal appointment slots, each with a start and end time. This list should be sorted by preference or efficiency.",
            ),
            Parameter(
                name="alternatives",
                param_type="list[datetime]",
                description="If no optimal slots are available, provide a list of alternative slots, clearly indicating that they are outside the preferred criteria.",
            ),
        ],
    )

    return ApplicationRequirements(
        name="Appointment Scheduler",
        context="The function for suggesting optimal appointment slots is designed to provide professionals and clients with the best possible meeting times based on the professional's availability, preferred working hours, and travel time considerations. This function operates in real-time, relying on input data without needing access to a database.",
        api_routes=[
            APIRouteRequirement(
                method="POST",
                path="/create_schedule",
                function_name="create_schedule",
                access_level=AccessLevel.PUBLIC,
                description="The function for suggesting optimal appointment slots is designed to provide professionals and clients with the best possible meeting times based on the professional's availability, preferred working hours, and travel time considerations. This function operates in real-time, relying on input data without needing access to a database.",
                request_model=appointment_model,
                response_model=appointment_response,
                database_schema=None,
            ),
        ],
    )


# Function to define requirements for the Distance Calculator
def distance_calculator_requirements() -> ApplicationRequirements:
    # Define request and response models here
    distance_model = RequestModel(
        name="DistanceInput",
        description="An object used to find the start and end locations",
        params=[
            Parameter(
                name="start_location",
                param_type="tuple[float, float]",
                description="The current location of the professional, provided as latitude and longitude coordinates.",
            ),
            Parameter(
                name="end_location",
                param_type="tuple[float,float]",
                description="The location where the client wishes to have the appointment, provided as latitude and longitude coordinates.",
            ),
        ],
    )

    distance_response = ResponseModel(
        name="DistanceOutput",
        description="Output of calcuating the distance",
        params=[
            Parameter(
                name="distance",
                param_type="tuple[float, float]",
                description="The calculated distance between the two locations, preferably in both kilometers and miles.",
            ),
            Parameter(
                name="travel_time",
                param_type="float",
                description="An estimation of the time it would take for the professional to travel from their location to the client's location in seconds, considering average travel conditions.",
            ),
        ],
    )

    return ApplicationRequirements(
        name="Distance Calculator",
        context="The Distance Calculator is a tool that calculates the distance between the professional's and the client's locations to aid in planning travel time for appointments.",
        api_routes=[
            APIRouteRequirement(
                method="POST",
                path="/calculate_distance",
                function_name="calculate_distance",
                access_level=AccessLevel.PUBLIC,
                description="Function that returns the distance for travel time based upon input",
                request_model=distance_model,
                response_model=distance_response,
                database_schema=None,
            ),
        ],
    )


def profile_management() -> ApplicationRequirements:
    # Define request and response models for each API route
    create_profile_request = RequestModel(
        name="CreateProfileRequest",
        description="Input required for creating a new profile",
        params=[
            Parameter(
                name="user_type",
                param_type="str",
                description="Type of the user: client or professional",
            ),
            Parameter(
                name="personal_details",
                param_type="dict[str, str]",
                description="Name and contact information",
            ),
            Parameter(
                name="preferences",
                param_type="dict[str, str]",
                description="Optional settings specific to the user type",
            ),
        ],
    )

    create_profile_response = ResponseModel(
        name="CreateProfileResponse",
        description="Output after creating a profile",
        params=[
            Parameter(
                name="message", param_type="str", description="Success or error message"
            ),
            Parameter(
                name="profile_details",
                param_type="dict[str, str]",
                description="Details of the created profile",
            ),
        ],
    )

    update_profile_request = RequestModel(
        name="UpdateProfileRequest",
        description="Input required for updating an existing profile",
        params=[
            Parameter(
                name="profile_id",
                param_type="str",
                description="Profile ID or unique identifier",
            ),
            Parameter(
                name="fields_to_update",
                param_type="dict[str, str]",
                description="Fields to be updated with their new values",
            ),
        ],
    )

    update_profile_response = ResponseModel(
        name="UpdateProfileResponse",
        description="Output after updating a profile",
        params=[
            Parameter(
                name="message", param_type="str", description="Success or error message"
            ),
            Parameter(
                name="updated_profile_details",
                param_type="dict[str, str]",
                description="Details of the updated profile",
            ),
        ],
    )

    retrieve_profile_request = RequestModel(
        name="RetrieveProfileRequest",
        description="Input required for retrieving a profile",
        params=[
            Parameter(
                name="profile_id",
                param_type="str",
                description="Profile ID or unique identifier",
            ),
        ],
    )

    retrieve_profile_response = ResponseModel(
        name="RetrieveProfileResponse",
        description="Output after retrieving a profile",
        params=[
            Parameter(
                name="profile_details",
                param_type="dict[str, str]",
                description="Details of the retrieved profile",
            ),
            Parameter(
                name="message",
                param_type="str",
                description="Error message if the profile is not found",
            ),
        ],
    )

    delete_profile_request = RequestModel(
        name="DeleteProfileRequest",
        description="Input required for deleting a profile",
        params=[
            Parameter(
                name="profile_id",
                param_type="str",
                description="Profile ID or unique identifier",
            ),
        ],
    )

    delete_profile_response = ResponseModel(
        name="DeleteProfileResponse",
        description="Output after deleting a profile",
        params=[
            Parameter(
                name="message",
                param_type="str",
                description="Success message confirming profile deletion or error message if the profile is not found or deletion fails",
            ),
        ],
    )

    # Define the database schema for profile management
    profiles_table = DatabaseTable(
        description="Stores user profile information",
        definition="""
        model Profile {
        id          Int     @id @default(autoincrement())
        user_type   String
        name        String
        contact     String
        preferences Json?
        }
        """,
    )

    profiles_schema = DatabaseSchema(
        name="ProfilesDatabase",
        description="Schema for storing client and professional profiles",
        tables=[profiles_table],
    )

    # Define API routes with their corresponding request and response models and link the database schema
    api_routes = [
        APIRouteRequirement(
            method="POST",
            path="/api/profile/create",
            function_name="create_profile",
            access_level=AccessLevel.PUBLIC,
            description="Creates a new user profile",
            request_model=create_profile_request,
            response_model=create_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="PUT",
            path="/api/profile/update",
            function_name="update_profile",
            access_level=AccessLevel.USER,
            description="Updates an existing user profile",
            request_model=update_profile_request,
            response_model=update_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="GET",
            path="/api/profile/retrieve",
            function_name="retrieve_profile",
            access_level=AccessLevel.USER,
            description="Retrieves a user profile",
            request_model=retrieve_profile_request,
            response_model=retrieve_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="DELETE",
            path="/api/profile/delete",
            function_name="delete_profile",
            access_level=AccessLevel.USER,
            description="Deletes a user profile",
            request_model=delete_profile_request,
            response_model=delete_profile_response,
            database_schema=profiles_schema,
        ),
    ]

    # Define the application requirements with the context and API routes
    application_requirements = ApplicationRequirements(
        name="Profile Management System",
        context="This system manages client and professional profiles, including operations for creating, updating, retrieving, and deleting profiles.",
        api_routes=api_routes,
    )

    # Output the full specification of the application
    return application_requirements


def tictactoe_game_requirements() -> ApplicationRequirements:
    request = RequestModel(
        name="TurnRequest",
        description="A request to make a move in the tictactoe game.",
        params=[
            Parameter(
                name="row",
                param_type="int",
                description="The row in which the move is made, the value should be between 1 and 3.",
            ),
            Parameter(
                name="col",
                param_type="int",
                description="The column in which the move is made, the value should be between 1 and 3.",
            ),
        ],
    )

    response = ResponseModel(
        name="GameStateResponse",
        description="A response containing the current state of the game.",
        params=[
            Parameter(
                name="gameId",
                param_type="str",
                description="The unique identifier of the game.",
            ),
            Parameter(
                name="turn",
                param_type="str",
                description="The current turn of the game. Possible values are 'X' or 'O'.",
            ),
            Parameter(
                name="state",
                param_type="str",
                description="The current state of the game. Possible values are 'In Progress', 'Draw', 'Win' or 'Loss'.",
            ),
            Parameter(
                name="board",
                param_type="str",
                description="Printed representation of the current game board.",
            ),
        ],
    )

    return ApplicationRequirements(
        name="TicTacToe Game",
        context="Two Players TicTacToe Game communicate through an API.",
        api_routes=[
            APIRouteRequirement(
                method="POST",
                path="/turn/{game_id}",
                function_name="make_turn",
                access_level=AccessLevel.PUBLIC,
                description="Function that allows a player to make a move and return the current state of the game. "
                "It will also initiate a new game if the game is not started.",
                request_model=request,
                response_model=response,
                database_schema=None,
            ),
        ],
    )


if __name__ == "__main__":
    from codex.common.logging_config import setup_logging

    setup_logging()
    logger.info(availability_checker_requirements())
    logger.info(invoice_generator_requirements())
    logger.info(appointment_optimization_requirements())
    logger.info(distance_calculator_requirements())
    logger.info(profile_management())
