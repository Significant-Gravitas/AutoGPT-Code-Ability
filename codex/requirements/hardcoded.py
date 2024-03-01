import logging

from prisma.enums import AccessLevel

from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    DatabaseSchema,
    DatabaseTable,
    EndpointDataModel,
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
                name="availablility_calendar",
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
                param_type="Tuple[float, float]",
                description="AThe current location of the professional, provided as latitude and longitude coordinates.",
            ),
            Parameter(
                name="end_location",
                param_type="Tuple[str,str]",
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
                param_type="dict",
                description="Name and contact information",
            ),
            Parameter(
                name="preferences",
                param_type="dict",
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
                param_type="dict",
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


def calendar_booking_system() -> ApplicationRequirements:
    database_schema = DatabaseSchema(
        name="TimeSyncSchema",
        description="A schema for the TimeSync app, supporting appointment scheduling, notifications, and calendar integrations.",
        tables=[
            DatabaseTable(
                name="User",
                description="Stores user information, including role and authentication details.",
                definition="model User {\\n  id        String        @id @default(uuid())\\n  email     String        @unique\\n  role      UserRole      @default(Client)\\n  password  String\\n  createdAt DateTime      @default(now())\\n  updatedAt DateTime      @updatedAt\\n  Appointments  Appointment[]\\n  Notifications Notification[]\\n  Integrations  Integration[]\\n}",
            ),
            DatabaseTable(
                name="Appointment",
                description="Represents appointments with status, type, and time zone information.",
                definition="model Appointment {\\n  id          String          @id @default(uuid())\\n  userId      String\\n  status      AppointmentStatus @default(Scheduled)\\n  type        String\\n  startTime   DateTime\\n  endTime     DateTime\\n  timeZone    String\\n  createdAt   DateTime        @default(now())\\n  updatedAt   DateTime        @updatedAt\\n  User        User            @relation(fields: [userId], references: [id])\\n  Notifications Notification[]\\n}",
            ),
            DatabaseTable(
                name="Notification",
                description="Manages notifications linked to users and appointments, with type defining the channels.",
                definition="model Notification {\\n  id            String        @id @default(uuid())\\n  userId        String\\n  appointmentId String\\n  type          NotificationType\\n  sentAt        DateTime?\\n  User          User          @relation(fields: [userId], references: [id])\\n  Appointment   Appointment   @relation(fields: [appointmentId], references: [id])\\n}",
            ),
            DatabaseTable(
                name="Integration",
                description="Handles external calendar integrations for users, storing details in a JSON format.",
                definition="model Integration {\\n  id        String        @id @default(uuid())\\n  userId    String\\n  type      IntegrationType\\n  details   Json\\n  User      User          @relation(fields: [userId], references: [id])\\n}",
            ),
        ],
    )
    return ApplicationRequirements(
        name="TimeSync",
        context="",
        api_routes=[
            APIRouteRequirement(
                method="POST",
                path="/users",
                function_name="create_user",
                description="Registers a new user by providing basic user information.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CreateUserInput",
                    description="CreateUserInput",
                    params=[
                        Parameter(
                            name="email",
                            param_type="string",
                            description="Unique email address of the user. Acts as a login identifier.",
                        ),
                        Parameter(
                            name="password",
                            param_type="string",
                            description="Password for the user account. Must comply with defined security standards.",
                        ),
                        Parameter(
                            name="role",
                            param_type="UserRole",
                            description="The role of the user which dictates access control. Optional parameter; defaults to 'Client' if not specified.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateUserInput",
                    description="CreateUserInput",
                    params=[
                        Parameter(
                            name="user_id",
                            param_type="string",
                            description="The unique identifier of the newly created user.",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="A success message confirming user creation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="PUT",
                path="/users/{id}",
                function_name="update_user_profile",
                description="Updates an existing user's profile information.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="UpdateUserProfileInput",
                    description="UpdateUserProfileInput",
                    params=[
                        Parameter(
                            name="email",
                            param_type="str",
                            description="The new email address of the user.",
                        ),
                        Parameter(
                            name="password",
                            param_type="str",
                            description="The new password of the user. Should be hashed in the database, not stored in plain text.",
                        ),
                        Parameter(
                            name="role",
                            param_type="UserRole",
                            description="The new role assigned to the user. Can be one of ['Admin', 'ServiceProvider', 'Client'].",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="UpdateUserProfileInput",
                    description="UpdateUserProfileInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="str",
                            description="The unique identifier of the user.",
                        ),
                        Parameter(
                            name="email",
                            param_type="str",
                            description="The updated email address of the user.",
                        ),
                        Parameter(
                            name="role",
                            param_type="UserRole",
                            description="The updated role assigned to the user.",
                        ),
                        Parameter(
                            name="updatedAt",
                            param_type="datetime",
                            description="The timestamp reflecting when the update was made.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="POST",
                path="/users/login",
                function_name="user_login",
                description="Authenticates a user and returns a session token.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    params=[
                        Parameter(
                            name="email",
                            param_type="str",
                            description="The email address associated with the user's account.",
                        ),
                        Parameter(
                            name="password",
                            param_type="str",
                            description="The password associated with the user's account.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the login was successful.",
                        ),
                        Parameter(
                            name="token",
                            param_type="str",
                            description="A session token to be used for authenticated requests.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A message providing more details about the login attempt, useful for debugging or informing the user about the login status.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="POST",
                path="/users/logout",
                function_name="user_logout",
                description="Logs out a user, invalidating the session token.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="UserLogoutInput",
                    description="UserLogoutInput",
                    params=[
                        Parameter(
                            name="Authorization",
                            param_type="Header",
                            description="The session token provided as a part of the HTTP header for authentication.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="UserLogoutInput",
                    description="UserLogoutInput",
                    params=[
                        Parameter(
                            name="message",
                            param_type="string",
                            description="A confirmation message indicating successful logout.",
                        )
                    ],
                ),
                database_schema=DatabaseSchema(
                    name="TimeSyncSchema",
                    description="A schema for the TimeSync app, supporting appointment scheduling, notifications, and calendar integrations.",
                    tables=[
                        DatabaseTable(
                            name="User",
                            description="Stores user information, including role and authentication details.",
                            definition="model User {\\n  id        String        @id @default(uuid())\\n  email     String        @unique\\n  role      UserRole      @default(Client)\\n  password  String\\n  createdAt DateTime      @default(now())\\n  updatedAt DateTime      @updatedAt\\n  Appointments  Appointment[]\\n  Notifications Notification[]\\n  Integrations  Integration[]\\n}",
                        ),
                        DatabaseTable(
                            name="Appointment",
                            description="Represents appointments with status, type, and time zone information.",
                            definition="model Appointment {\\n  id          String          @id @default(uuid())\\n  userId      String\\n  status      AppointmentStatus @default(Scheduled)\\n  type        String\\n  startTime   DateTime\\n  endTime     DateTime\\n  timeZone    String\\n  createdAt   DateTime        @default(now())\\n  updatedAt   DateTime        @updatedAt\\n  User        User            @relation(fields: [userId], references: [id])\\n  Notifications Notification[]\\n}",
                        ),
                        DatabaseTable(
                            name="Notification",
                            description="Manages notifications linked to users and appointments, with type defining the channels.",
                            definition="model Notification {\\n  id            String        @id @default(uuid())\\n  userId        String\\n  appointmentId String\\n  type          NotificationType\\n  sentAt        DateTime?\\n  User          User          @relation(fields: [userId], references: [id])\\n  Appointment   Appointment   @relation(fields: [appointmentId], references: [id])\\n}",
                        ),
                        DatabaseTable(
                            name="Integration",
                            description="Handles external calendar integrations for users, storing details in a JSON format.",
                            definition="model Integration {\\n  id        String        @id @default(uuid())\\n  userId    String\\n  type      IntegrationType\\n  details   Json\\n  User      User          @relation(fields: [userId], references: [id])\\n}",
                        ),
                    ],
                ),
                data_models=[],
            ),
            APIRouteRequirement(
                method="PUT",
                path="/users/{id}/settings/notifications",
                function_name="update_notification_settings",
                description="Updates a user's notification preferences.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="UpdateNotificationSettingsRequest",
                    description="UpdateNotificationSettingsRequest",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="string",
                            description="The unique identifier of the user whose notification settings need to be updated.",
                        ),
                        # Parameter(
                        #     name="settings",
                        #     param_type="NotificationSettingsUpdate",
                        #     description="The new notification settings to be applied to the user's profile.",
                        # ),
                        Parameter(
                            name="emailFrequency",
                            param_type="string",
                            description="The desired frequency of email notifications ('daily', 'weekly', 'never').",
                        ),
                        Parameter(
                            name="smsEnabled",
                            param_type="boolean",
                            description="Indicates whether SMS notifications are enabled (true/false).",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="UpdateNotificationSettingsRequest",
                    description="UpdateNotificationSettingsRequest",
                    params=[
                        Parameter(
                            name="success",
                            param_type="boolean",
                            description="Indicates if the update operation was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="A message detailing the outcome of the operation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    # EndpointDataModel(
                    #     name="NotificationSettingsUpdate",
                    #     description="Defines the fields available for updating a user's notification preferences, like frequency and method.",
                    #     params=[
                    #         Parameter(
                    #             name="emailFrequency",
                    #             param_type="string",
                    #             description="The desired frequency of email notifications ('daily', 'weekly', 'never').",
                    #         ),
                    #         Parameter(
                    #             name="smsEnabled",
                    #             param_type="boolean",
                    #             description="Indicates whether SMS notifications are enabled (true/false).",
                    #         ),
                    #     ],
                    # )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/appointments",
                function_name="create_appointment",
                description="Creates a new appointment.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="CreateAppointmentInput",
                    description="CreateAppointmentInput",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="str",
                            description="The ID of the user creating the appointment.",
                        ),
                        Parameter(
                            name="startTime",
                            param_type="datetime",
                            description="The start time for the appointment.",
                        ),
                        Parameter(
                            name="endTime",
                            param_type="datetime",
                            description="The end time for the appointment.",
                        ),
                        Parameter(
                            name="type",
                            param_type="str",
                            description="Type of the appointment.",
                        ),
                        Parameter(
                            name="participants",
                            param_type="[str]",
                            description="List of participating user IDs.",
                        ),
                        Parameter(
                            name="timeZone",
                            param_type="str",
                            description="Timezone for the scheduled appointment.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateAppointmentInput",
                    description="CreateAppointmentInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates success or failure of the operation.",
                        ),
                        Parameter(
                            name="appointmentId",
                            param_type="str",
                            description="Unique identifier for the newly created appointment.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="Additional information or error message.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="PUT",
                path="/appointments/{id}",
                function_name="update_appointment",
                description="Updates details of an existing appointment.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="AppointmentUpdateInput",
                    description="AppointmentUpdateInput",
                    params=[
                        Parameter(
                            name="startTime",
                            param_type="datetime",
                            description="The new start time for the appointment, accounting for any time zone considerations.",
                        ),
                        Parameter(
                            name="endTime",
                            param_type="datetime",
                            description="The new end time for the appointment, ensuring it follows logically after the start time.",
                        ),
                        Parameter(
                            name="type",
                            param_type="str",
                            description="Optionally update the type/category of the appointment.",
                        ),
                        Parameter(
                            name="status",
                            param_type="AppointmentStatus",
                            description="The updated status to reflect any changes such as rescheduling or cancellations.",
                        ),
                        Parameter(
                            name="timeZone",
                            param_type="str",
                            description="If the time zone needs adjusting to reflect the appropriate scheduling context.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="AppointmentUpdateInput",
                    description="AppointmentUpdateInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="str",
                            description="The ID of the appointment that was updated.",
                        ),
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates true if the appointment was successfully updated, false otherwise.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="Provides more information about the outcome of the update, such as 'Appointment updated successfully' or 'Update failed due to [reason]'.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="DELETE",
                path="/appointments/{id}",
                function_name="cancel_appointment",
                description="Cancels an existing appointment.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="CancelAppointmentInput",
                    description="CancelAppointmentInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="str",
                            description="Unique identifier of the appointment to be canceled.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="CancelAppointmentInput",
                    description="CancelAppointmentInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates whether the appointment cancellation was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A message detailing the outcome of the cancellation request.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="PUT",
                path="/notifications/settings",
                function_name="configure_notifications",
                description="Configures a user's notification preferences.",
                access_level=AccessLevel.USER,
                request_model=RequestModel(
                    name="ConfigureNotificationsRequest",
                    description="ConfigureNotificationsRequest",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="string",
                            description="The unique identifier of the user updating their preferences",
                        ),
                        Parameter(
                            name="emailEnabled",
                            param_type="boolean",
                            description="Indicates whether email notifications are enabled",
                        ),
                        Parameter(
                            name="emailFrequency",
                            param_type="string",
                            description="Defines how often email notifications are sent ('immediately', 'daily', 'weekly')",
                        ),
                        Parameter(
                            name="smsEnabled",
                            param_type="boolean",
                            description="Indicates whether SMS notifications are enabled",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="ConfigureNotificationsRequest",
                    description="ConfigureNotificationsRequest",
                    params=[
                        Parameter(
                            name="success",
                            param_type="boolean",
                            description="Indicates whether the update operation was successful",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="Provides information about the operation's outcome or failure reason",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    # EndpointDataModel(
                    #     name="NotificationSettings",
                    #     description="Defines the notification preferences for a user, including channels and frequency",
                    #     params=[
                    #         Parameter(
                    #             name="emailEnabled",
                    #             param_type="boolean",
                    #             description="Indicates whether email notifications are enabled",
                    #         ),
                    #         Parameter(
                    #             name="emailFrequency",
                    #             param_type="string",
                    #             description="Defines how often email notifications are sent ('immediately', 'daily', 'weekly')",
                    #         ),
                    #         Parameter(
                    #             name="smsEnabled",
                    #             param_type="boolean",
                    #             description="Indicates whether SMS notifications are enabled",
                    #         ),
                    #     ],
                    # )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/notifications/dispatch",
                function_name="dispatch_notifications",
                description="Sends out notifications based on predefined criteria and user settings.",
                access_level=AccessLevel.ADMIN,
                request_model=RequestModel(
                    name="DispatchNotificationInput",
                    description="DispatchNotificationInput",
                    params=[
                        Parameter(
                            name="criteria",
                            param_type="string",
                            description="Criteria for notification dispatch, such as 'allPendingWithin24h' to indicate all notifications for appointments occurring in the next 24 hours.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="DispatchNotificationInput",
                    description="DispatchNotificationInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="boolean",
                            description="If the dispatch was successful overall.",
                        ),
                        Parameter(
                            name="dispatchedCount",
                            param_type="int",
                            description="Total number of notifications dispatched.",
                        ),
                        Parameter(
                            name="failedCount",
                            param_type="int",
                            description="Number of notifications that failed to dispatch.",
                        ),
                        Parameter(
                            name="errors",
                            param_type="[string]",
                            description="List of errors for individual failures, if applicable.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
        ],
    )


def inventory_mgmt_system() -> ApplicationRequirements:
    database_schema = DatabaseSchema(
        name="InvenTrackSchema",
        description="This schema defines the structure for the InvenTrack inventory management system, including users, inventory items, orders, reports, batches, and locations.",
        tables=[
            DatabaseTable(
                name="User",
                description="Stores user information including their role.",
                definition="model User {\\n  id        Int    @id @default(autoincrement())\\n  email     String @unique\\n  password  String\\n  role      Role\\n  orders    Order[]\\n  alerts    Alert[]\\n}",
            ),
            DatabaseTable(
                name="InventoryItem",
                description="Represents an inventory item, including name, description, quantity, and which location/batch it belongs to.",
                definition="model InventoryItem {\\n  id          Int      @id @default(autoincrement())\\n  name        String\\n  description String?\\n  quantity    Int\\n  locationId  Int\\n  batchId     Int\\n  location    Location @relation(fields: [locationId], references: [id])\\n  batch       Batch    @relation(fields: [batchId], references: [id])\\n}",
            ),
            DatabaseTable(
                name="Order",
                description="Tracks orders made by users, whether automated or manual.",
                definition="model Order {\\n  id        Int       @id @default(autoincrement())\\n  userId    Int\\n  itemId    Int\\n  quantity  Int\\n  orderType OrderType\\n  user      User      @relation(fields: [userId], references: [id])\\n  item      InventoryItem @relation(fields: [itemId], references: [id])\\n}",
            ),
            DatabaseTable(
                name="Report",
                description="Stores reports generated by users about inventory.",
                definition="model Report {\\n  id      Int     @id @default(autoincrement())\\n  userId  Int\\n  content String\\n  user    User    @relation(fields: [userId], references: [id])\\n}",
            ),
            DatabaseTable(
                name="Batch",
                description="Defines a batch of items, particularly for perishables with an expiry date.",
                definition="model Batch {\\n  id             Int             @id @default(autoincrement())\\n  expirationDate DateTime\\n  items          InventoryItem[]\\n}",
            ),
            DatabaseTable(
                name="Location",
                description="Represents a physical location or warehouse where inventory is stored.",
                definition="model Location {\\n  id    Int              @id @default(autoincrement())\\n  name  String\\n  address String\\n  items InventoryItem[]\\n}",
            ),
            DatabaseTable(
                name="Alert",
                description="Customizable alerts set by users for tracking inventory levels.",
                definition="model Alert {\\n  id        Int       @id @default(autoincrement())\\n  userId    Int\\n  criteria  String\\n  threshold Int\\n  user      User      @relation(fields: [userId], references: [id])\\n}",
            ),
            DatabaseTable(
                name="Integration",
                description="Details the external business systems that InvenTrack integrates with.",
                definition="model Integration {\\n  id         Int        @id @default(autoincrement())\\n  systemType SystemType\\n  details    String?\\n}",
            ),
        ],
    )
    return ApplicationRequirements(
        name="InvenTrack",
        context="A tool designed to handle the tracking of inventory levels and usage for each client service. This includes the capability to add, update, and delete inventory items. To facilitate these functionalities, a set of API endpoints will be implemented.",
        api_routes=[
            APIRouteRequirement(
                method="GET",
                path="/inventory",
                function_name="list_inventory",
                description="Fetch a list of inventory items.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="ListInventoryRequest",
                    description="ListInventoryRequest",
                    params=[
                        Parameter(
                            name="filters",
                            param_type="InventoryFilter",
                            description="Optional filters to apply when listing inventory items.",
                        ),
                        Parameter(
                            name="pagination",
                            param_type="PaginationParams",
                            description="Optional pagination control parameters.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="ListInventoryRequest",
                    description="ListInventoryRequest",
                    params=[
                        Parameter(
                            name="items",
                            param_type="array[InventoryItem]",
                            description="A list of inventory items that match the request criteria.",
                        ),
                        Parameter(
                            name="totalItems",
                            param_type="int",
                            description="The total number of inventory items that match the request filters, ignoring pagination.",
                        ),
                        Parameter(
                            name="currentPage",
                            param_type="int",
                            description="The current page number of the inventory items list.",
                        ),
                        Parameter(
                            name="totalPages",
                            param_type="int",
                            description="The total number of pages available based on the current filter and pagination settings.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="InventoryFilter",
                        description="Optional filters for listing inventory items, including filter by location, batch, and name.",
                        params=[
                            Parameter(
                                name="locationId",
                                param_type="int",
                                description="Allows filtering inventory items by their stored location ID.",
                            ),
                            Parameter(
                                name="batchId",
                                param_type="int",
                                description="Allows filtering inventory items by their associated batch ID.",
                            ),
                            Parameter(
                                name="name",
                                param_type="string",
                                description="Allows filtering inventory items by a name or partial name match.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="PaginationParams",
                        description="Parameters for controlling the pagination of the list_inventory response.",
                        params=[
                            Parameter(
                                name="page",
                                param_type="int",
                                description="Specifies the page number of inventory items to retrieve.",
                            ),
                            Parameter(
                                name="pageSize",
                                param_type="int",
                                description="Specifies the number of inventory items per page.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="PUT",
                path="/inventory/{id}",
                function_name="update_inventory_item",
                description="Update an inventory item's details.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="UpdateInventoryItemInput",
                    description="UpdateInventoryItemInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="int",
                            description="the unique identifier of the inventory item to update",
                        ),
                        Parameter(
                            name="name",
                            param_type="str",
                            description="optional: the new name of the inventory item",
                        ),
                        Parameter(
                            name="description",
                            param_type="str",
                            description="optional: the new description of the inventory item",
                        ),
                        Parameter(
                            name="quantity",
                            param_type="int",
                            description="optional: the new quantity of the inventory item",
                        ),
                        Parameter(
                            name="locationId",
                            param_type="int",
                            description="optional: the new location identifier where the inventory item is stored",
                        ),
                        Parameter(
                            name="batchId",
                            param_type="int",
                            description="optional: the new batch identifier associated with the inventory item",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="UpdateInventoryItemInput",
                    description="UpdateInventoryItemInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="indicates if the update operation was successful",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="provides details on the outcome of the operation, including error messages",
                        ),
                        Parameter(
                            name="updatedItem",
                            param_type="InventoryItem",
                            description="optional: the updated inventory item details, provided if the update was successful",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="POST",
                path="/inventory",
                function_name="create_inventory_item",
                description="Add a new inventory item.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CreateInventoryItemRequest",
                    description="CreateInventoryItemRequest",
                    params=[
                        Parameter(
                            name="inventoryItem",
                            param_type="InventoryItemCreateInput",
                            description="Object containing details necessary for adding a new inventory item.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateInventoryItemRequest",
                    description="CreateInventoryItemRequest",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the item was successfully created.",
                        ),
                        Parameter(
                            name="itemId",
                            param_type="int",
                            description="The ID of the newly created inventory item.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A descriptive message about the result of the operation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="InventoryItemCreateInput",
                        description="Defines the necessary parameters for creating a new inventory item, including name, quantity, and optionally description, locationId, and batchId for perishables.",
                        params=[
                            Parameter(
                                name="name",
                                param_type="str",
                                description="The name of the inventory item.",
                            ),
                            Parameter(
                                name="description",
                                param_type="str",
                                description="A brief description of the inventory item. Optional.",
                            ),
                            Parameter(
                                name="quantity",
                                param_type="int",
                                description="The initial stock quantity of the inventory item.",
                            ),
                            Parameter(
                                name="locationId",
                                param_type="int",
                                description="The ID of the location where the inventory item is stored. Optional.",
                            ),
                            Parameter(
                                name="batchId",
                                param_type="int",
                                description="Related batch ID for perishable goods. Optional.",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="DELETE",
                path="/inventory/{id}",
                function_name="delete_inventory_item",
                description="Remove an inventory item.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="DeleteInventoryItemInput",
                    description="DeleteInventoryItemInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="int",
                            description="The unique identifier of the inventory item to be deleted.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="DeleteInventoryItemInput",
                    description="DeleteInventoryItemInput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates whether the deletion was successful.",
                        ),
                        Parameter(
                            name="error_message",
                            param_type="str",
                            description="Provides an error message if the deletion was not successful. This field is optional and may not be present if 'success' is true.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="POST",
                path="/reports",
                function_name="create_report",
                description="Generate a new report based on provided parameters.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CreateReportRequest",
                    description="CreateReportRequest",
                    params=[
                        Parameter(
                            name="reportParams",
                            param_type="CreateReportParams",
                            description="Object containing all necessary parameters to create a report.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateReportRequest",
                    description="CreateReportRequest",
                    params=[
                        Parameter(
                            name="result",
                            param_type="CreateReportResponse",
                            description="Object containing the result of the report creation attempt.",
                        )
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="CreateReportParams",
                        description="Defines the parameters required for creating a new inventory report.",
                        params=[
                            Parameter(
                                name="dateRange",
                                param_type="DateRange",
                                description="The date range for which the report should cover.",
                            ),
                            Parameter(
                                name="reportType",
                                param_type="str",
                                description="Specifies the type of report to generate, such as 'inventoryLevel', 'reordering', or 'expiryTracking'.",
                            ),
                            Parameter(
                                name="inventoryItems",
                                param_type="List[int]",
                                description="Optional. A list of inventory item IDs to include in the report. If not provided, the report covers all items.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="CreateReportResponse",
                        description="The response returned after attempting to create a report. Contains the report's ID if successful.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the report was successfully created.",
                            ),
                            Parameter(
                                name="reportId",
                                param_type="int",
                                description="The unique identifier of the newly created report. Null if 'success' is false.",
                            ),
                            Parameter(
                                name="message",
                                param_type="str",
                                description="A message detailing the outcome of the request.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="GET",
                path="/reports",
                function_name="get_reports",
                description="List all available reports.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="GetReportsRequest", description="GetReportsRequest", params=[]
                ),
                response_model=ResponseModel(
                    name="GetReportsResponse",
                    description="GetReportsResponse",
                    params=[
                        Parameter(
                            name="reports",
                            param_type="list of ReportSummary",
                            description="A list of report summaries",
                        ),
                        Parameter(
                            name="totalCount",
                            param_type="int",
                            description="The total number of reports available",
                        ),
                        Parameter(
                            name="page",
                            param_type="int",
                            description="The current page number",
                        ),
                        Parameter(
                            name="pageSize",
                            param_type="int",
                            description="The number of items per page",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="ReportSummary",
                        description="Summarizes essential details of a report for listing purposes.",
                        params=[
                            Parameter(
                                name="id",
                                param_type="int",
                                description="Unique identifier of the report",
                            ),
                            Parameter(
                                name="title",
                                param_type="str",
                                description="Title of the report",
                            ),
                            Parameter(
                                name="creationDate",
                                param_type="datetime",
                                description="The date and time when the report was created",
                            ),
                            Parameter(
                                name="description",
                                param_type="str",
                                description="A brief description of the report",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/integrations",
                function_name="create_integration",
                description="Register a new integration with an external system.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CreateIntegrationInput",
                    description="CreateIntegrationInput",
                    params=[
                        Parameter(
                            name="systemType",
                            param_type="string",
                            description="The type of system to integrate.",
                        ),
                        Parameter(
                            name="details",
                            param_type="string",
                            description="Configuration details for the integration.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateIntegrationOutput",
                    description="CreateIntegrationOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the operation was successful.",
                        ),
                        Parameter(
                            name="integrationId",
                            param_type="int",
                            description="ID of the created integration, if successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="Outcome message.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="CreateIntegrationInput",
                        description="Parameters required to register a new external system integration.",
                        params=[
                            Parameter(
                                name="systemType",
                                param_type="string",
                                description="The type of system being integrated; defines the integration protocol or standard.",
                            ),
                            Parameter(
                                name="details",
                                param_type="string",
                                description="Configuration details necessary for establishing the connection with the external system.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="CreateIntegrationResponse",
                        description="The output after successfully registering a new integration.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the integration was successfully created.",
                            ),
                            Parameter(
                                name="integrationId",
                                param_type="int",
                                description="The unique identifier of the newly created integration. Provided only if success is true.",
                            ),
                            Parameter(
                                name="message",
                                param_type="string",
                                description="A message describing the outcome of the operation.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="GET",
                path="/integrations",
                function_name="list_integrations",
                description="List all external system integrations.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="ListIntegrationsRequest",
                    description="ListIntegrationsRequest",
                    params=[],
                ),
                response_model=ResponseModel(
                    name="ListIntegrationsResponse",
                    description="ListIntegrationsResponse",
                    params=[
                        Parameter(
                            name="integrations",
                            param_type="List[IntegrationSummary]",
                            description="A list of integration summaries detailing the available external system integrations.",
                        )
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="IntegrationSummary",
                        description="Summarizes essential details of an external system integration for listing purposes.",
                        params=[
                            Parameter(
                                name="id",
                                param_type="int",
                                description="Unique identifier of the integration.",
                            ),
                            Parameter(
                                name="systemType",
                                param_type="str",
                                description="Type of the external system (e.g., Sales, Procurement).",
                            ),
                            Parameter(
                                name="details",
                                param_type="str",
                                description="Additional details or description of the integration.",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/alerts",
                function_name="create_alert",
                description="Set a new alert based on inventory criteria.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CreateAlertInput",
                    description="CreateAlertInput",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="int",
                            description="The ID of the user setting the alert.",
                        ),
                        Parameter(
                            name="criteria",
                            param_type="string",
                            description="Condition or event that triggers the alert.",
                        ),
                        Parameter(
                            name="threshold",
                            param_type="int",
                            description="Numeric value that triggers the alert when reached or exceeded.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="CreateAlertOutput",
                    description="CreateAlertOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the alert creation was successful.",
                        ),
                        Parameter(
                            name="alertId",
                            param_type="int",
                            description="The ID of the newly created alert if successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="Descriptive message of the alert creation outcome.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="CreateAlertInput",
                        description="Describes the input required to create a new alert.",
                        params=[
                            Parameter(
                                name="userId",
                                param_type="int",
                                description="The ID of the user setting the alert.",
                            ),
                            Parameter(
                                name="criteria",
                                param_type="string",
                                description="The condition that triggers the alert.",
                            ),
                            Parameter(
                                name="threshold",
                                param_type="int",
                                description="The numeric value that, when reached or exceeded, triggers the alert.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="CreateAlertOutput",
                        description="Contains confirmation of the alert creation, including the newly created alert's ID.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates whether the alert was successfully created.",
                            ),
                            Parameter(
                                name="alertId",
                                param_type="int",
                                description="The unique identifier of the newly created alert, provided when 'success' is true.",
                            ),
                            Parameter(
                                name="message",
                                param_type="string",
                                description="A message describing the outcome of the alert creation attempt.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="GET",
                path="/alerts",
                function_name="list_alerts",
                description="List all configured alerts.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="ListAlertsRequest", description="ListAlertsRequest", params=[]
                ),
                response_model=ResponseModel(
                    name="ListAlertsResponse",
                    description="ListAlertsResponse",
                    params=[
                        Parameter(
                            name="alerts",
                            param_type="List[AlertDetail]",
                            description="List containing detailed configurations of all alerts.",
                        )
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="POST",
                path="/auth/login",
                function_name="user_login",
                description="Authenticate a user and provide token.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    params=[
                        Parameter(
                            name="email",
                            param_type="str",
                            description="The user's email address.",
                        ),
                        Parameter(
                            name="password",
                            param_type="str",
                            description="The user's account password.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="UserLoginOutput",
                    description="UserLoginOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="True if the login was successful, false otherwise.",
                        ),
                        Parameter(
                            name="token",
                            param_type="str",
                            description="JWT token generated for the session if login is successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="Descriptive message about the login attempt.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="UserLoginInput",
                        description="Captures user login credentials.",
                        params=[
                            Parameter(
                                name="email",
                                param_type="str",
                                description="The email address associated with the user's account.",
                            ),
                            Parameter(
                                name="password",
                                param_type="str",
                                description="The password for the user's account.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="UserLoginOutput",
                        description="Contains the result of the login attempt, including a token if successful.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the login was successful.",
                            ),
                            Parameter(
                                name="token",
                                param_type="str",
                                description="The authentication token provided upon successful login. Null if login failed.",
                            ),
                            Parameter(
                                name="message",
                                param_type="str",
                                description="A message describing the outcome of the login attempt.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/auth/logout",
                function_name="user_logout",
                description="Logs out a user, invalidating the session token.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="LogoutInput", description="LogoutInput", params=[]
                ),
                response_model=ResponseModel(
                    name="LogoutOutput",
                    description="LogoutOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates whether the logout was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="string",
                            description="Message providing more details on the outcome. It can indicate success or describe why the logout failed.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="GET",
                path="/auth/permissions/{userid}",
                function_name="check_permissions",
                description="Verify if a user has permissions for a specific action.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="CheckPermissionsInput",
                    description="CheckPermissionsInput",
                    params=[
                        Parameter(
                            name="userid",
                            param_type="int",
                            description="The unique identifier of the user.",
                        ),
                        Parameter(
                            name="action",
                            param_type="str",
                            description="Specific action or permission to check for. Optional; could be structured to check against multiple actions.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="CheckPermissionsOutput",
                    description="CheckPermissionsOutput",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="int",
                            description="The ID of the user whose permissions were checked.",
                        ),
                        Parameter(
                            name="permissions",
                            param_type="list[PermissionCheckResult]",
                            description="A list of results for each action's permission check.",
                        ),
                    ],
                ),
                database_schema=database_schema,
                data_models=[
                    EndpointDataModel(
                        name="PermissionCheckResult",
                        description="Represents the result of checking a user's permissions.",
                        params=[
                            Parameter(
                                name="hasPermission",
                                param_type="bool",
                                description="Indicates whether the user has the requested permission.",
                            ),
                            Parameter(
                                name="message",
                                param_type="str",
                                description="Provides additional information about the permission check, e.g., granted, denied, or reason for denial.",
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


def invoice_payment_tracking() -> ApplicationRequirements:
    schema = DatabaseSchema(
        name="FinFlow",
        description="Prisma schema for FinFlow, a backend system for managing financing, invoicing, and payments.",
        tables=[
            DatabaseTable(
                name="User",
                description="Represents system users with different roles.",
                definition="model User {\n  id    String  @id @default(cuid())\n  email String  @unique\n  role  Role\n  invoices Invoice[]\n  reports Report[]\n}",
            ),
            DatabaseTable(
                name="Invoice",
                description="Invoicing information, related to users and payments.",
                definition="model Invoice {\n  id     String        @id @default(cuid())\n  userId String\n  user   User          @relation(fields: [userId], references: [id])\n  number String @unique\n  status InvoiceStatus\n  items  InvoiceItem[]\n  payment Payment?\n}",
            ),
            DatabaseTable(
                name="InvoiceItem",
                description="Line items associated with invoices.",
                definition="model InvoiceItem {\n  id        String  @id @default(cuid())\n  invoiceId String\n  invoice   Invoice @relation(fields: [invoiceId], references: [id])\n  description String\n  quantity Int\n  price   Float\n}",
            ),
            DatabaseTable(
                name="Payment",
                description="Payment details linked to invoices and payment gateways.",
                definition="model Payment {\n  id        String @id @default(cuid())\n  invoiceId String\n  invoice   Invoice @relation(fields: [invoiceId], references: [id])\n  amount    Float\n  gatewayId String\n  gateway   PaymentGateway @relation(fields: [gatewayId], references: [id])\n}",
            ),
            DatabaseTable(
                name="Report",
                description="Financial reports generated for the user.",
                definition="model Report {\n  id          String      @id @default(cuid())\n  userId      String\n  user        User        @relation(fields: [userId], references: [id])\n  type        ReportType\n  generatedAt DateTime\n}",
            ),
            DatabaseTable(
                name="PaymentGateway",
                description="Information about payment gateways.",
                definition="model PaymentGateway {\n  id    String    @id @default(cuid())\n  name  String\n  apiKey String\n  payments Payment[]\n}",
            ),
            DatabaseTable(
                name="ComplianceLog",
                description="Log for compliance and auditing.",
                definition="model ComplianceLog {\n  id         String    @id @default(cuid())\n  description String\n  loggedAt   DateTime\n}",
            ),
        ],
    )

    return ApplicationRequirements(
        name="FinFlow",
        context="The backend for managnig invoicing, tracking payments, and handling financial reports and insights it should consist of robust API routes to handle  functionalities related to financial transactions. \n\n### Project Description\nBased on the detailed information gathered through the interview process, the task entails developing a backend system focusing on managing invoicing, tracking payments, and facilitating comprehensive financial reports and insights. ",
        api_routes=[
            APIRouteRequirement(
                method="POST",
                path="/invoices",
                function_name="create_invoice",
                description="Creates a new invoice in the system.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="InvoiceCreationRequest",
                    description="InvoiceCreationRequest",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="str",
                            description="Identifier for the user who is creating the invoice.",
                        ),
                        Parameter(
                            name="items",
                            param_type="List[InvoiceItemInput]",
                            description="Array of line items to be included in the invoice.",
                        ),
                        Parameter(
                            name="currency",
                            param_type="str",
                            description="Currency in which the invoice is being issued.",
                        ),
                        Parameter(
                            name="taxRate",
                            param_type="float",
                            description="Tax rate applicable to the invoice, represented as a percentage.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="InvoiceCreationResponse",
                    description="InvoiceCreationResponse",
                    params=[
                        Parameter(
                            name="invoiceId",
                            param_type="str",
                            description="Unique identifier for the newly created invoice.",
                        ),
                        Parameter(
                            name="status",
                            param_type="str",
                            description="Status of the invoice after creation. Expected values are 'Draft' or 'Finalized'.",
                        ),
                        Parameter(
                            name="creationDate",
                            param_type="datetime",
                            description="Timestamp reflecting when the invoice was created.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="InvoiceCreationInput",
                        description="Model for input required to create a new invoice. This includes information about the invoice itself, the line items, and more.",
                        params=[
                            Parameter(
                                name="userId",
                                param_type="str",
                                description="The ID of the user creating the invoice.",
                            ),
                            Parameter(
                                name="items",
                                param_type="List[InvoiceItemInput]",
                                description="A collection of line items including description, quantity, and price.",
                            ),
                            Parameter(
                                name="currency",
                                param_type="str",
                                description="Currency code (e.g., USD, EUR) for the invoice.",
                            ),
                            Parameter(
                                name="taxRate",
                                param_type="float",
                                description="Applicable tax rate for the invoice, if any.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="InvoiceItemInput",
                        description="Details for each item included in the invoice.",
                        params=[
                            Parameter(
                                name="description",
                                param_type="str",
                                description="Description of the line item.",
                            ),
                            Parameter(
                                name="quantity",
                                param_type="int",
                                description="Quantity of the line item.",
                            ),
                            Parameter(
                                name="price",
                                param_type="float",
                                description="Price per unit of the line item.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/invoices/{id}",
                function_name="edit_invoice",
                description="Edits an existing invoice by ID.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="EditInvoiceInput",
                    description="EditInvoiceInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="str",
                            description="The unique identifier of the invoice to be edited.",
                        ),
                        Parameter(
                            name="invoiceDetails",
                            param_type="InvoiceEditModel",
                            description="The details of the invoice to be edited, encapsulated within the InvoiceEditModel.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="EditInvoiceOutput",
                    description="EditInvoiceOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates whether the edit operation was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A message describing the result of the operation, particularly useful in case of failure.",
                        ),
                        Parameter(
                            name="updatedInvoice",
                            param_type="Invoice",
                            description="The updated invoice object reflecting the changes made. Null if operation failed.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="InvoiceEditModel",
                        description="Model for editing invoice details, allowing updates to various invoice fields while ensuring that changes to critical fields like currency or finalized status are handled with caution.",
                        params=[
                            Parameter(
                                name="status",
                                param_type="String (Optional)",
                                description="Allows modifying the status of the invoice, i.e., from draft to finalized, but with strict checks to prevent arbitrary status changes.",
                            ),
                            Parameter(
                                name="items",
                                param_type="Array[ItemEditModel] (Optional)",
                                description="List of line items to be added or updated in the invoice. Each item modification is described in a separate model.",
                            ),
                            Parameter(
                                name="currency",
                                param_type="String (Optional)",
                                description="Currency in which the invoice is denoted. Modifications should ensure no discrepancies in already entered amounts.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="ItemEditModel",
                        description="Model for adding or editing line items within an invoice.",
                        params=[
                            Parameter(
                                name="description",
                                param_type="str",
                                description="Description of the invoice item.",
                            ),
                            Parameter(
                                name="quantity",
                                param_type="int",
                                description="Quantity of the item.",
                            ),
                            Parameter(
                                name="price",
                                param_type="float",
                                description="Price per unit of the item.",
                            ),
                            Parameter(
                                name="id",
                                param_type="String (Optional)",
                                description="Unique ID of the item if it exists. If provided, the item will be updated; otherwise, a new item will be added.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="GET",
                path="/invoices/{id}",
                function_name="get_invoice",
                description="Retrieves invoice details by ID.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="GetInvoiceInput",
                    description="GetInvoiceInput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="string",
                            description="The unique ID of the invoice to retrieve.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="GetInvoiceOutput",
                    description="GetInvoiceOutput",
                    params=[
                        Parameter(
                            name="id",
                            param_type="string",
                            description="The unique ID of the invoice.",
                        ),
                        Parameter(
                            name="number",
                            param_type="string",
                            description="The unique invoice number.",
                        ),
                        Parameter(
                            name="status",
                            param_type="string",
                            description="Current status of the invoice (e.g., draft, finalized).",
                        ),
                        Parameter(
                            name="items",
                            param_type="array of InvoiceItem",
                            description="A collection of line items associated with the invoice. Each item contains details such as description, quantity, and price.",
                        ),
                        Parameter(
                            name="payment",
                            param_type="Payment or null",
                            description="Payment details associated with this invoice. Null if no payment has been made yet.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[],
            ),
            APIRouteRequirement(
                method="GET",
                path="/invoices",
                function_name="list_invoices",
                description="Lists all invoices related to a user.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="ListInvoicesRequest",
                    description="ListInvoicesRequest",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="str",
                            description="The unique identifier of the user whose invoices are to be listed.",
                        ),
                        Parameter(
                            name="page",
                            param_type="int",
                            description="Pagination parameter, denotes the page number of the invoice list to be retrieved.",
                        ),
                        Parameter(
                            name="pageSize",
                            param_type="int",
                            description="Pagination parameter, denotes the number of invoices to be listed per page.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="ListInvoicesResponse",
                    description="ListInvoicesResponse",
                    params=[
                        Parameter(
                            name="invoices",
                            param_type="List[InvoiceSummary]",
                            description="An array of invoice summary objects.",
                        ),
                        Parameter(
                            name="total",
                            param_type="int",
                            description="Total number of invoices available for the user.",
                        ),
                        Parameter(
                            name="currentPage",
                            param_type="int",
                            description="The current page number being returned in the response.",
                        ),
                        Parameter(
                            name="pageSize",
                            param_type="int",
                            description="The number of invoices returned per page.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="InvoiceSummary",
                        description="A concise model representing the key information of an invoice for listing purposes.",
                        params=[
                            Parameter(
                                name="invoiceId",
                                param_type="str",
                                description="Unique identifier for the invoice.",
                            ),
                            Parameter(
                                name="invoiceNumber",
                                param_type="str",
                                description="The unique number associated with the invoice.",
                            ),
                            Parameter(
                                name="status",
                                param_type="str",
                                description="Current status of the invoice (e.g., draft, finalized).",
                            ),
                            Parameter(
                                name="totalAmount",
                                param_type="float",
                                description="Total amount of the invoice, taking into account item prices and quantities.",
                            ),
                            Parameter(
                                name="currency",
                                param_type="str",
                                description="The currency in which the invoice was issued.",
                            ),
                            Parameter(
                                name="createdAt",
                                param_type="datetime",
                                description="The date and time when the invoice was created.",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/payments/initiate/{invoiceId}",
                function_name="initiate_payment",
                description="Initiates a payment for an invoice.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="PaymentInitiationRequest",
                    description="PaymentInitiationRequest",
                    params=[
                        Parameter(
                            name="invoiceId",
                            param_type="str",
                            description="Unique ID of the invoice for which the payment is being initiated.",
                        ),
                        Parameter(
                            name="gatewayId",
                            param_type="str",
                            description="Identifier of the payment gateway through which the payment will be processed.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="PaymentInitiationResponse",
                    description="PaymentInitiationResponse",
                    params=[
                        Parameter(
                            name="paymentId",
                            param_type="str",
                            description="Unique identifier for the payment transaction, provided by the system.",
                        ),
                        Parameter(
                            name="status",
                            param_type="str",
                            description="Status of the payment initiation, which could be 'Pending', 'Failed', or other relevant terms.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="PaymentInitiationRequest",
                        description="Model for initiating a payment, requires the invoice ID and payment gateway details.",
                        params=[
                            Parameter(
                                name="invoiceId",
                                param_type="str",
                                description="The unique identifier for the invoice being paid.",
                            ),
                            Parameter(
                                name="gatewayId",
                                param_type="str",
                                description="The identifier for the chosen payment gateway.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="PaymentInitiationResponse",
                        description="Provides the outcome of the payment initiation request, including a transaction status and unique payment identifier.",
                        params=[
                            Parameter(
                                name="paymentId",
                                param_type="str",
                                description="A unique identifier generated for the initiated payment.",
                            ),
                            Parameter(
                                name="status",
                                param_type="str",
                                description="The status of the payment initiation, e.g., 'Pending', 'Failed'.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/payments/confirm/{paymentId}",
                function_name="confirm_payment",
                description="Confirms a payment has been completed.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="PaymentConfirmationRequest",
                    description="PaymentConfirmationRequest",
                    params=[
                        Parameter(
                            name="paymentId",
                            param_type="str",
                            description="The unique identifier of the payment to be confirmed.",
                        ),
                        Parameter(
                            name="confirmationStatus",
                            param_type="str",
                            description="Indicates the status of the payment confirmation attempt.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="PaymentConfirmationResponse",
                    description="PaymentConfirmationResponse",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Boolean flag indicating if the payment confirmation was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A message providing more details on the confirmation status.",
                        ),
                        Parameter(
                            name="updatedPaymentDetails",
                            param_type="Payment",
                            description="The updated payment details post-confirmation attempt, reflecting the new status and any additional updates.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="PaymentConfirmationInput",
                        description="Input model for confirming payments, capturing necessary details for processing the payment confirmation.",
                        params=[
                            Parameter(
                                name="paymentId",
                                param_type="str",
                                description="Unique identifier for the payment to be confirmed.",
                            ),
                            Parameter(
                                name="confirmationStatus",
                                param_type="str",
                                description="The status of the payment confirmation, e.g., 'Confirmed', 'Failed'.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="PaymentConfirmationResponse",
                        description="Response model for the payment confirmation process, indicating the success or failure of the operation.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the payment confirmation was successful.",
                            ),
                            Parameter(
                                name="message",
                                param_type="str",
                                description="A descriptive message about the outcome of the payment confirmation.",
                            ),
                            Parameter(
                                name="updatedPaymentDetails",
                                param_type="Payment",
                                description="The updated payment details post-confirmation.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/notifications/remind",
                function_name="send_reminder",
                description="Sends a reminder for an unpaid invoice.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="ReminderNotificationInput",
                    description="ReminderNotificationInput",
                    params=[
                        Parameter(
                            name="invoiceId",
                            param_type="str",
                            description="Unique identifier for the invoice the reminder pertains to.",
                        ),
                        Parameter(
                            name="userId",
                            param_type="str",
                            description="Unique identifier for the user associated with the invoice to send the notification to.",
                        ),
                        Parameter(
                            name="medium",
                            param_type="str",
                            description="Preferred medium of notification (e.g., Email, SMS).",
                        ),
                        Parameter(
                            name="sendTime",
                            param_type="datetime",
                            description="Scheduled time for sending the reminder.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="ReminderNotificationOutput",
                    description="ReminderNotificationOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the reminder was successfully sent.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A descriptive message about the outcome of the attempt.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="ReminderNotificationInput",
                        description="Model for input required to send a reminder notification about an unpaid invoice, including invoice and user details.",
                        params=[
                            Parameter(
                                name="invoiceId",
                                param_type="str",
                                description="Unique identifier for the invoice the reminder pertains to.",
                            ),
                            Parameter(
                                name="userId",
                                param_type="str",
                                description="Unique identifier for the user associated with the invoice to send the notification to.",
                            ),
                            Parameter(
                                name="medium",
                                param_type="str",
                                description="Preferred medium of notification (e.g., Email, SMS).",
                            ),
                            Parameter(
                                name="sendTime",
                                param_type="datetime",
                                description="Scheduled time for sending the reminder.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="ReminderNotificationOutput",
                        description="Model for output after attempting to send a reminder notification about an unpaid invoice.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the reminder was successfully sent.",
                            ),
                            Parameter(
                                name="message",
                                param_type="str",
                                description="A descriptive message about the outcome of the attempt.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/reports/generate",
                function_name="generate_report",
                description="Generates a financial report based on specified parameters.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="GenerateReportInput",
                    description="GenerateReportInput",
                    params=[
                        Parameter(
                            name="userId",
                            param_type="str",
                            description="The user's ID for whom the report is being generated.",
                        ),
                        Parameter(
                            name="reportType",
                            param_type="str",
                            description="Specifies the type of financial report required.",
                        ),
                        Parameter(
                            name="startDate",
                            param_type="datetime",
                            description="The start date for the reporting period.",
                        ),
                        Parameter(
                            name="endDate",
                            param_type="datetime",
                            description="The end date for the reporting period.",
                        ),
                        Parameter(
                            name="filters",
                            param_type="List[str]",
                            description="Optional filters to refine the report data.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="GenerateReportOutput",
                    description="GenerateReportOutput",
                    params=[
                        Parameter(
                            name="report",
                            param_type="FinancialReport",
                            description="The detailed financial report generated based on the input parameters.",
                        )
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="ReportRequestParameters",
                        description="Contains all the parameters needed to generate a customizable financial report.",
                        params=[
                            Parameter(
                                name="userId",
                                param_type="str",
                                description="Unique identifier of the user requesting the report.",
                            ),
                            Parameter(
                                name="reportType",
                                param_type="str",
                                description="Type of the report required (e.g., revenue_growth, expense_tracking).",
                            ),
                            Parameter(
                                name="startDate",
                                param_type="datetime",
                                description="Start date for the time frame of the report.",
                            ),
                            Parameter(
                                name="endDate",
                                param_type="datetime",
                                description="End date for the time frame of the report.",
                            ),
                            Parameter(
                                name="filters",
                                param_type="List[str]",
                                description="List of additional filters to apply to the report data (optional).",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="FinancialReport",
                        description="Represents the structured output of a financial report, including various metrics and insights.",
                        params=[
                            Parameter(
                                name="reportType",
                                param_type="str",
                                description="Type of the generated report.",
                            ),
                            Parameter(
                                name="generatedAt",
                                param_type="datetime",
                                description="Timestamp of when the report was generated.",
                            ),
                            Parameter(
                                name="metrics",
                                param_type="List[ReportMetric]",
                                description="A collection of metrics included in the report.",
                            ),
                            Parameter(
                                name="insights",
                                param_type="List[str]",
                                description="List of insights derived from the report data.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="ReportMetric",
                        description="Details of a single metric within the financial report.",
                        params=[
                            Parameter(
                                name="metricName",
                                param_type="str",
                                description="Name of the metric.",
                            ),
                            Parameter(
                                name="value",
                                param_type="float",
                                description="Quantitative value of the metric.",
                            ),
                            Parameter(
                                name="unit",
                                param_type="str",
                                description="Unit of measurement for the metric.",
                            ),
                            Parameter(
                                name="description",
                                param_type="str",
                                description="A brief description or insight related to the metric.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="GET",
                path="/insights",
                function_name="fetch_insights",
                description="Provides strategic financial insights.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="FinancialInsightsRequest",
                    description="FinancialInsightsRequest",
                    params=[
                        Parameter(
                            name="startDate",
                            param_type="datetime",
                            description="The start date for the range of financial data to consider.",
                        ),
                        Parameter(
                            name="endDate",
                            param_type="datetime",
                            description="The end date for the range of financial data to consider.",
                        ),
                        Parameter(
                            name="metrics",
                            param_type="List[str]",
                            description="Optional. A list of specific financial metrics to retrieve insights for.",
                        ),
                    ],
                ),
                response_model=ResponseModel(
                    name="FinancialInsightsResponse",
                    description="FinancialInsightsResponse",
                    params=[
                        Parameter(
                            name="insights",
                            param_type="List[FinancialInsight]",
                            description="A collection of financial insights.",
                        )
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="FinancialInsight",
                        description="Represents a high-level financial insight derived from aggregating financial data.",
                        params=[
                            Parameter(
                                name="label",
                                param_type="str",
                                description="The name of the financial insight or metric.",
                            ),
                            Parameter(
                                name="value",
                                param_type="float",
                                description="The numerical value of the insight.",
                            ),
                            Parameter(
                                name="trend",
                                param_type="str",
                                description="Indicates the trend of this metric (e.g., 'increasing', 'decreasing', 'stable').",
                            ),
                            Parameter(
                                name="interpretation",
                                param_type="str",
                                description="A brief expert analysis or interpretation of what this insight suggests about the business's financial health.",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/security/settings",
                function_name="update_security_settings",
                description="Updates security settings and protocols.",
                access_level=AccessLevel.ADMIN,
                request_model=RequestModel(
                    name="UpdateSecuritySettingsRequest",
                    description="UpdateSecuritySettingsRequest",
                    params=[
                        Parameter(
                            name="updates",
                            param_type="List[SecuritySettingUpdate]",
                            description="A list of security settings to update, each indicating the setting name and its new value.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="UpdateSecuritySettingsResponse",
                    description="UpdateSecuritySettingsResponse",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the update operation was successful.",
                        ),
                        Parameter(
                            name="updatedSettings",
                            param_type="List[SecuritySettingUpdate]",
                            description="A list of all settings that were successfully updated.",
                        ),
                        Parameter(
                            name="failedSettings",
                            param_type="List[SecuritySettingUpdate]",
                            description="A list of settings that failed to update, with descriptions of the failure reasons.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="SecuritySettingUpdate",
                        description="Represents a security setting that needs to be updated.",
                        params=[
                            Parameter(
                                name="settingName",
                                param_type="str",
                                description="The name of the security setting to update.",
                            ),
                            Parameter(
                                name="newValue",
                                param_type="str",
                                description="The new value for the security setting.",
                            ),
                        ],
                    ),
                    EndpointDataModel(
                        name="UpdateSecuritySettingsResponse",
                        description="Response model for update security settings operation, indicating success or failure.",
                        params=[
                            Parameter(
                                name="success",
                                param_type="bool",
                                description="Indicates if the update operation was successful.",
                            ),
                            Parameter(
                                name="updatedSettings",
                                param_type="List[SecuritySettingUpdate]",
                                description="A list of all settings that were successfully updated.",
                            ),
                            Parameter(
                                name="failedSettings",
                                param_type="List[SecuritySettingUpdate]",
                                description="A list of settings that failed to update, with descriptions of the failure reasons.",
                            ),
                        ],
                    ),
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/compliance/logs",
                function_name="log_compliance_action",
                description="Records a compliance-related action for auditing.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="LogComplianceActionInput",
                    description="LogComplianceActionInput",
                    params=[
                        Parameter(
                            name="complianceAction",
                            param_type="ComplianceAction",
                            description="The compliance action that needs to be logged.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="LogComplianceActionOutput",
                    description="LogComplianceActionOutput",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates whether the logging was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="A descriptive message regarding the outcome of the log attempt.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="ComplianceAction",
                        description="Represents a compliance-related action that needs to be logged for auditing.",
                        params=[
                            Parameter(
                                name="actionType",
                                param_type="str",
                                description="The type of action performed, e.g., 'Data Update', 'View Sensitive Information', etc.",
                            ),
                            Parameter(
                                name="description",
                                param_type="str",
                                description="A detailed description of the action performed.",
                            ),
                            Parameter(
                                name="performedBy",
                                param_type="str",
                                description="Identifier for the user or system component that performed the action.",
                            ),
                            Parameter(
                                name="timestamp",
                                param_type="datetime",
                                description="Timestamp when the action was performed.",
                            ),
                        ],
                    )
                ],
            ),
            APIRouteRequirement(
                method="POST",
                path="/integration/payment-gateway",
                function_name="connect_payment_gateway",
                description="Sets up connection with a specified payment gateway.",
                access_level=AccessLevel.PUBLIC,
                request_model=RequestModel(
                    name="PaymentGatewayConnectionRequest",
                    description="PaymentGatewayConnectionRequest",
                    params=[
                        Parameter(
                            name="connectionDetails",
                            param_type="PaymentGatewayConnectionInput",
                            description="An object holding the necessary connection details.",
                        )
                    ],
                ),
                response_model=ResponseModel(
                    name="PaymentGatewayConnectionResponse",
                    description="PaymentGatewayConnectionResponse",
                    params=[
                        Parameter(
                            name="success",
                            param_type="bool",
                            description="Indicates if the connection attempt was successful.",
                        ),
                        Parameter(
                            name="message",
                            param_type="str",
                            description="Provides more detail on the connection status, including errors if any.",
                        ),
                        Parameter(
                            name="gatewayId",
                            param_type="Optional[str]",
                            description="The unique identifier for the gateway in the system, provided upon a successful connection.",
                        ),
                    ],
                ),
                database_schema=schema,
                data_models=[
                    EndpointDataModel(
                        name="PaymentGatewayConnectionInput",
                        description="Data required to initiate a connection with a payment gateway.",
                        params=[
                            Parameter(
                                name="gatewayName",
                                param_type="str",
                                description="The name of the payment gateway to connect.",
                            ),
                            Parameter(
                                name="apiKey",
                                param_type="str",
                                description="The API key provided by the payment gateway for authentication.",
                            ),
                            Parameter(
                                name="apiSecret",
                                param_type="str",
                                description="The API secret or other credentials required for secure access.",
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


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
                name="column",
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
    logger.info(calendar_booking_system())
    logger.info(inventory_mgmt_system())
    logger.info(invoice_payment_tracking())
