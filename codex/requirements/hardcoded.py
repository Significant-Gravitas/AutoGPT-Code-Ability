from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    DatabaseSchema,
    DatabaseTable,
    Parameter,
    RequestModel,
    ResponseModel,
)


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


# Function to define requirements for the Invoice Generator
def invoice_generator_requirements() -> ApplicationRequirements:
    # Define request and response models here
    invoice_model = RequestModel(
        name="invoicemodel",
        description="An object used to generte an invoice",
        params=[
            Parameter(
                name="services_rendered",
                param_type="List[Tuple[float, string, List[Tuple[str, str, float, float]]]]",
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


# Function to define requirements for the Appointment Optimization Tool
def appointment_optimization_requirements() -> ApplicationRequirements:
    # Define request and response models here
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
                param_type="datetime[]",
                description="A list of optimal appointment slots, each with a start and end time. This list should be sorted by preference or efficiency.",
            ),
            Parameter(
                name="alternatives",
                param_type="datetime[]",
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
                description="Function that returns the availability of professionals, updating based on current activity or schedule.",
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
                param_type="dict",
                description="Name and contact information",
            ),
            Parameter(
                name="preferences",
                param_type="dict",
                description="Optional settings specific to the user type",
                optional=True,
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
                param_type="dict",
                description="Details of the created profile",
                optional=True,
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
                param_type="dict",
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
                param_type="dict",
                description="Details of the updated profile",
                optional=True,
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
                param_type="dict",
                description="Details of the retrieved profile",
                optional=True,
            ),
            Parameter(
                name="message",
                param_type="str",
                description="Error message if the profile is not found",
                optional=True,
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
            description="Creates a new user profile",
            request_model=create_profile_request,
            response_model=create_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="PUT",
            path="/api/profile/update",
            description="Updates an existing user profile",
            request_model=update_profile_request,
            response_model=update_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="GET",
            path="/api/profile/retrieve",
            description="Retrieves a user profile",
            request_model=retrieve_profile_request,
            response_model=retrieve_profile_response,
            database_schema=profiles_schema,
        ),
        APIRouteRequirement(
            method="DELETE",
            path="/api/profile/delete",
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



def appointment_scheduling_system() -> ApplicationRequirements:
    
    return ApplicationRequirements(
        
    )