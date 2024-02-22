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
                function_name="create_invoice",
                access_level=AccessLevel.PUBLIC,
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
                function_name="create_schedule",
                access_level=AccessLevel.PUBLIC,
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
                            param_type="String",
                            description="The new email address of the user.",
                        ),
                        Parameter(
                            name="password",
                            param_type="String",
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
                            param_type="String",
                            description="The unique identifier of the user.",
                        ),
                        Parameter(
                            name="email",
                            param_type="String",
                            description="The updated email address of the user.",
                        ),
                        Parameter(
                            name="role",
                            param_type="UserRole",
                            description="The updated role assigned to the user.",
                        ),
                        Parameter(
                            name="updatedAt",
                            param_type="DateTime",
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
                            param_type="String",
                            description="The ID of the user creating the appointment.",
                        ),
                        Parameter(
                            name="startTime",
                            param_type="DateTime",
                            description="The start time for the appointment.",
                        ),
                        Parameter(
                            name="endTime",
                            param_type="DateTime",
                            description="The end time for the appointment.",
                        ),
                        Parameter(
                            name="type",
                            param_type="String",
                            description="Type of the appointment.",
                        ),
                        Parameter(
                            name="participants",
                            param_type="[String]",
                            description="List of participating user IDs.",
                        ),
                        Parameter(
                            name="timeZone",
                            param_type="String",
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
                            param_type="Boolean",
                            description="Indicates success or failure of the operation.",
                        ),
                        Parameter(
                            name="appointmentId",
                            param_type="String",
                            description="Unique identifier for the newly created appointment.",
                        ),
                        Parameter(
                            name="message",
                            param_type="String",
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
                            param_type="DateTime",
                            description="The new start time for the appointment, accounting for any time zone considerations.",
                        ),
                        Parameter(
                            name="endTime",
                            param_type="DateTime",
                            description="The new end time for the appointment, ensuring it follows logically after the start time.",
                        ),
                        Parameter(
                            name="type",
                            param_type="String",
                            description="Optionally update the type/category of the appointment.",
                        ),
                        Parameter(
                            name="status",
                            param_type="AppointmentStatus",
                            description="The updated status to reflect any changes such as rescheduling or cancellations.",
                        ),
                        Parameter(
                            name="timeZone",
                            param_type="String",
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
                            param_type="String",
                            description="The ID of the appointment that was updated.",
                        ),
                        Parameter(
                            name="success",
                            param_type="Boolean",
                            description="Indicates true if the appointment was successfully updated, false otherwise.",
                        ),
                        Parameter(
                            name="message",
                            param_type="String",
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


if __name__ == "__main__":
    from codex.common.logging_config import setup_logging

    setup_logging()
    logger.info(availability_checker_requirements())
    logger.info(invoice_generator_requirements())
    logger.info(appointment_optimization_requirements())
    logger.info(distance_calculator_requirements())
    logger.info(profile_management())
    logger.info(calendar_booking_system())
