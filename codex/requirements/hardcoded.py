import logging

from prisma.enums import AccessLevel

from codex.common.model import (
    ObjectTypeModel as ObjectTypeModel,
    ObjectFieldModel as ObjectFieldE,
)
from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    DatabaseSchema,
    DatabaseTable,
)

logger = logging.getLogger(__name__)


def availability_checker_requirements() -> ApplicationRequirements:
    # Define request and response models here
    check_availability_request = ObjectTypeModel(
        name="CheckAvailabilityRequest",
        description="A request to check the availability status of a professional based on the current time and their schedule.",
        Fields=[
            ObjectFieldE(
                name="current_time",
                type="datetime",
                description="The timestamp at which the availability status is being requested.",
            ),
            ObjectFieldE(
                name="schedule_data",
                type="list[tuple[datetime, datetime]]",
                description="A list of tuples representing the schedule of the professional, where each tuple contains start and end times of appointments or busy periods.",
            ),
        ],
    )

    # Response Model for availability status
    availability_status_response = ObjectTypeModel(
        name="AvailabilityStatusResponse",
        description="A response indicating the current availability status of the professional.",
        Fields=[
            ObjectFieldE(
                name="availability_status",
                type="str",
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
    invoice_model = ObjectTypeModel(
        name="InvoiceRequest",
        description="An object used to generte an invoice",
        Fields=[
            ObjectFieldE(
                name="services_rendered",
                type="list[tuple[float, str, list[tuple[str, str, float, float]]]]",
                description="a list of the services being rendered broken down by hours, service_description, and items used for the service. Items used is further broken down by name, description, unit_cost, and units used",
            ),
            ObjectFieldE(
                name="tax_rate",
                type="float",
                description="local tax rate used for calculations",
            ),
        ],
    )

    invoice_response = ObjectTypeModel(
        name="InvoiceResponse",
        description="A pdf of an invoice",
        Fields=[
            ObjectFieldE(
                name="file_data",
                type="bytes",
                description="A PDF file for the invoice",
            ),
            ObjectFieldE(
                name="file_name",
                type="str",
                description="The name of the PDF file",
            ),
            ObjectFieldE(
                name="mime_type",
                type="str",
                description="The mime type for the response",
            ),
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
    appointment_model = ObjectTypeModel(
        name="AppointmentModel",
        description="An object used to make good times for an appointment",
        Fields=[
            ObjectFieldE(
                name="availability_calendar",
                type="list[datetime]",
                description="A data structure (like a list) containing the professional's available time slots for a given period (e.g., a week). Each time slot should include the start and end times.",
            ),
            ObjectFieldE(
                name="prefered_hours",
                type="str",
                description="The professional's preferred working hours (e.g., 9 AM to 5 PM), which could be a default setting or specified for each day.",
            ),
            ObjectFieldE(
                name="travel_time_buffer",
                type="time",
                description="Information regarding the time needed to travel between appointments. This could be a fixed duration or vary based on the time of day or location.",
            ),
            ObjectFieldE(
                name="time_frame",
                type="str",
                description="The time frame during which the client wishes to schedule the appointment (e.g., a specific date or range of dates).",
            ),
        ],
    )

    appointment_response = ObjectTypeModel(
        name="AppointmentResponse",
        description="A few good times for appointments",
        Fields=[
            ObjectFieldE(
                name="slots",
                type="list[datetime]",
                description="A list of optimal appointment slots, each with a start and end time. This list should be sorted by preference or efficiency.",
            ),
            ObjectFieldE(
                name="alternatives",
                type="list[datetime]",
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
    distance_model = ObjectTypeModel(
        name="DistanceInput",
        description="An object used to find the start and end locations",
        Fields=[
            ObjectFieldE(
                name="start_location",
                type="tuple[float, float]",
                description="The current location of the professional, provided as latitude and longitude coordinates.",
            ),
            ObjectFieldE(
                name="end_location",
                type="tuple[float,float]",
                description="The location where the client wishes to have the appointment, provided as latitude and longitude coordinates.",
            ),
        ],
    )

    distance_response = ObjectTypeModel(
        name="DistanceOutput",
        description="Output of calcuating the distance",
        Fields=[
            ObjectFieldE(
                name="distance",
                type="tuple[float, float]",
                description="The calculated distance between the two locations, preferably in both kilometers and miles.",
            ),
            ObjectFieldE(
                name="travel_time",
                type="float",
                description="An estimation of the time it would take for the professional to travel from their location to the client's location, considering average travel conditions.",
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
    create_profile_request = ObjectTypeModel(
        name="CreateProfileRequest",
        description="Input required for creating a new profile",
        Fields=[
            ObjectFieldE(
                name="user_type",
                type="str",
                description="Type of the user: client or professional",
            ),
            ObjectFieldE(
                name="personal_details",
                type="dict[str, str]",
                description="Name and contact information",
            ),
            ObjectFieldE(
                name="preferences",
                type="dict[str, str]",
                description="Optional settings specific to the user type",
            ),
        ],
    )

    create_profile_response = ObjectTypeModel(
        name="CreateProfileResponse",
        description="Output after creating a profile",
        Fields=[
            ObjectFieldE(
                name="message", type="str", description="Success or error message"
            ),
            ObjectFieldE(
                name="profile_details",
                type="dict[str, str]",
                description="Details of the created profile",
            ),
        ],
    )

    update_profile_request = ObjectTypeModel(
        name="UpdateProfileRequest",
        description="Input required for updating an existing profile",
        Fields=[
            ObjectFieldE(
                name="profile_id",
                type="str",
                description="Profile ID or unique identifier",
            ),
            ObjectFieldE(
                name="fields_to_update",
                type="dict[str, str]",
                description="Fields to be updated with their new values",
            ),
        ],
    )

    update_profile_response = ObjectTypeModel(
        name="UpdateProfileResponse",
        description="Output after updating a profile",
        Fields=[
            ObjectFieldE(
                name="message", type="str", description="Success or error message"
            ),
            ObjectFieldE(
                name="updated_profile_details",
                type="dict[str, str]",
                description="Details of the updated profile",
            ),
        ],
    )

    retrieve_profile_request = ObjectTypeModel(
        name="RetrieveProfileRequest",
        description="Input required for retrieving a profile",
        Fields=[
            ObjectFieldE(
                name="profile_id",
                type="str",
                description="Profile ID or unique identifier",
            ),
        ],
    )

    retrieve_profile_response = ObjectTypeModel(
        name="RetrieveProfileResponse",
        description="Output after retrieving a profile",
        Fields=[
            ObjectFieldE(
                name="profile_details",
                type="dict[str, str]",
                description="Details of the retrieved profile",
            ),
            ObjectFieldE(
                name="message",
                type="str",
                description="Error message if the profile is not found",
            ),
        ],
    )

    delete_profile_request = ObjectTypeModel(
        name="DeleteProfileRequest",
        description="Input required for deleting a profile",
        Fields=[
            ObjectFieldE(
                name="profile_id",
                type="str",
                description="Profile ID or unique identifier",
            ),
        ],
    )

    delete_profile_response = ObjectTypeModel(
        name="DeleteProfileResponse",
        description="Output after deleting a profile",
        Fields=[
            ObjectFieldE(
                name="message",
                type="str",
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
            description="Creates a new user profile and stores it in the database",
            request_model=create_profile_request,
            response_model=create_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="PUT",
            path="/api/profile/update",
            function_name="update_profile",
            access_level=AccessLevel.USER,
            description="Updates an existing user profile in the database",
            request_model=update_profile_request,
            response_model=update_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="GET",
            path="/api/profile/retrieve",
            function_name="retrieve_profile",
            access_level=AccessLevel.USER,
            description="Retrieves a user profile from the database",
            request_model=retrieve_profile_request,
            response_model=retrieve_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="DELETE",
            path="/api/profile/delete",
            function_name="delete_profile",
            access_level=AccessLevel.USER,
            description="Deletes a user profile from the database",
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
    request = ObjectTypeModel(
        name="TurnRequest",
        description="A request to make a move in the tictactoe game.",
        Fields=[
            ObjectFieldE(
                name="game_id",
                type="str",
                description="The unique identifier of the game.",
            ),
            ObjectFieldE(
                name="row",
                type="int",
                description="The row in which the move is made, the value should be between 1 and 3.",
            ),
            ObjectFieldE(
                name="col",
                type="int",
                description="The column in which the move is made, the value should be between 1 and 3.",
            ),
        ],
    )

    response = ObjectTypeModel(
        name="GameStateResponse",
        description="A response containing the current state of the game.",
        Fields=[
            ObjectFieldE(
                name="game_id",
                type="str",
                description="The unique identifier of the game.",
            ),
            ObjectFieldE(
                name="turn",
                type="str",
                description="The current turn of the game. Possible values are 'X' or 'O'.",
            ),
            ObjectFieldE(
                name="state",
                type="str",
                description="The current state of the game. Possible values are 'In Progress', 'Draw', 'Win' or 'Loss'.",
            ),
            ObjectFieldE(
                name="board",
                type="str",
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
