import logging

from prisma.enums import AccessLevel

from codex.common.model import (
    ObjectTypeModel as ObjectTypeE,
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
    check_availability_request = ObjectTypeE(
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
    availability_status_response = ObjectTypeE(
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
    invoice_model = ObjectTypeE(
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

    invoice_response = ObjectTypeE(
        name="InvoiceResponse",
        description="A pdf of an invoice",
        Fields=[
            ObjectFieldE(
                name="availability_status",
                type="file",
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
    appointment_model = ObjectTypeE(
        name="AppointmentModel",
        description="An object used to make good times for an appointment",
        Fields=[
            ObjectFieldE(
                name="availability_calendar",
                type="list[datetime]",
                description="A data structure (like a list or array) containing the professional's available time slots for a given period (e.g., a week). Each time slot should include the start and end times.",
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

    appointment_response = ObjectTypeE(
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
                type="datetime[]",
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
    distance_model = ObjectTypeE(
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

    distance_response = ObjectTypeE(
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
                type="time",
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
    create_profile_request = ObjectTypeE(
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
                type="dict",
                description="Name and contact information",
            ),
            ObjectFieldE(
                name="preferences",
                type="dict",
                description="Optional settings specific to the user type",
            ),
        ],
    )

    create_profile_response = ObjectTypeE(
        name="CreateProfileResponse",
        description="Output after creating a profile",
        Fields=[
            ObjectFieldE(
                name="message", type="str", description="Success or error message"
            ),
            ObjectFieldE(
                name="profile_details",
                type="dict",
                description="Details of the created profile",
            ),
        ],
    )

    update_profile_request = ObjectTypeE(
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
                type="dict",
                description="Fields to be updated with their new values",
            ),
        ],
    )

    update_profile_response = ObjectTypeE(
        name="UpdateProfileResponse",
        description="Output after updating a profile",
        Fields=[
            ObjectFieldE(
                name="message", type="str", description="Success or error message"
            ),
            ObjectFieldE(
                name="updated_profile_details",
                type="dict",
                description="Details of the updated profile",
            ),
        ],
    )

    retrieve_profile_request = ObjectTypeE(
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

    retrieve_profile_response = ObjectTypeE(
        name="RetrieveProfileResponse",
        description="Output after retrieving a profile",
        Fields=[
            ObjectFieldE(
                name="profile_details",
                type="dict",
                description="Details of the retrieved profile",
            ),
            ObjectFieldE(
                name="message",
                type="str",
                description="Error message if the profile is not found",
            ),
        ],
    )

    delete_profile_request = ObjectTypeE(
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

    delete_profile_response = ObjectTypeE(
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
                request_model=ObjectTypeE(
                    name="CreateUserInput",
                    description="CreateUserInput",
                    Fields=[
                        ObjectFieldE(
                            name="email",
                            type="str",
                            description="Unique email address of the user. Acts as a login identifier.",
                        ),
                        ObjectFieldE(
                            name="password",
                            type="str",
                            description="Password for the user account. Must comply with defined security standards.",
                        ),
                        ObjectFieldE(
                            name="role",
                            type="UserRole",
                            description="The role of the user which dictates access control. Optional ObjectFieldE; defaults to 'Client' if not specified.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateUserInput",
                    description="CreateUserInput",
                    Fields=[
                        ObjectFieldE(
                            name="user_id",
                            type="str",
                            description="The unique identifier of the newly created user.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A success message confirming user creation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="PUT",
                path="/users/{id}",
                function_name="update_user_profile",
                description="Updates an existing user's profile information.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="UpdateUserProfileInput",
                    description="UpdateUserProfileInput",
                    Fields=[
                        ObjectFieldE(
                            name="email",
                            type="str",
                            description="The new email address of the user.",
                        ),
                        ObjectFieldE(
                            name="password",
                            type="str",
                            description="The new password of the user. Should be hashed in the database, not stored in plain text.",
                        ),
                        ObjectFieldE(
                            name="role",
                            type="UserRole",
                            description="The new role assigned to the user. Can be one of ['Admin', 'ServiceProvider', 'Client'].",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UpdateUserProfileInput",
                    description="UpdateUserProfileInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="The unique identifier of the user.",
                        ),
                        ObjectFieldE(
                            name="email",
                            type="str",
                            description="The updated email address of the user.",
                        ),
                        ObjectFieldE(
                            name="role",
                            type="UserRole",
                            description="The updated role assigned to the user.",
                        ),
                        ObjectFieldE(
                            name="updatedAt",
                            type="datetime",
                            description="The timestamp reflecting when the update was made.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/users/login",
                function_name="user_login",
                description="Authenticates a user and returns a session token.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    Fields=[
                        ObjectFieldE(
                            name="email",
                            type="str",
                            description="The email address associated with the user's account.",
                        ),
                        ObjectFieldE(
                            name="password",
                            type="str",
                            description="The password associated with the user's account.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the login was successful.",
                        ),
                        ObjectFieldE(
                            name="token",
                            type="str",
                            description="A session token to be used for authenticated requests.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A message providing more details about the login attempt, useful for debugging or informing the user about the login status.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/users/logout",
                function_name="user_logout",
                description="Logs out a user, invalidating the session token.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="UserLogoutInput",
                    description="UserLogoutInput",
                    Fields=[
                        ObjectFieldE(
                            name="Authorization",
                            type="Header",
                            description="The session token provided as a part of the HTTP header for authentication.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UserLogoutOutput",
                    description="UserLogoutOutput",
                    Fields=[
                        ObjectFieldE(
                            name="message",
                            type="str",
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
            ),
            APIRouteRequirement(
                method="PUT",
                path="/users/{id}/settings/notifications",
                function_name="update_notification_settings",
                description="Updates a user's notification preferences.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="UpdateNotificationSettingsRequest",
                    description="UpdateNotificationSettingsRequest",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="The unique identifier of the user whose notification settings need to be updated.",
                        ),
                        # ObjectFieldE(
                        #     name="settings",
                        #     type="NotificationSettingsUpdate",
                        #     description="The new notification settings to be applied to the user's profile.",
                        # ),
                        ObjectFieldE(
                            name="emailFrequency",
                            type="str",
                            description="The desired frequency of email notifications ('daily', 'weekly', 'never').",
                        ),
                        ObjectFieldE(
                            name="smsEnabled",
                            type="bool",
                            description="Indicates whether SMS notifications are enabled (true/false).",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UpdateNotificationSettingsResponse",
                    description="UpdateNotificationSettingsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the update operation was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A message detailing the outcome of the operation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/appointments",
                function_name="create_appointment",
                description="Creates a new appointment.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="CreateAppointmentInput",
                    description="CreateAppointmentInput",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="The ID of the user creating the appointment.",
                        ),
                        ObjectFieldE(
                            name="startTime",
                            type="datetime",
                            description="The start time for the appointment.",
                        ),
                        ObjectFieldE(
                            name="endTime",
                            type="datetime",
                            description="The end time for the appointment.",
                        ),
                        ObjectFieldE(
                            name="type",
                            type="str",
                            description="Type of the appointment.",
                        ),
                        ObjectFieldE(
                            name="participants",
                            type="[str]",
                            description="List of participating user IDs.",
                        ),
                        ObjectFieldE(
                            name="timeZone",
                            type="str",
                            description="Timezone for the scheduled appointment.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateAppointmentOutput",
                    description="CreateAppointmentOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates success or failure of the operation.",
                        ),
                        ObjectFieldE(
                            name="appointmentId",
                            type="str",
                            description="Unique identifier for the newly created appointment.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Additional information or error message.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="PUT",
                path="/appointments/{id}",
                function_name="update_appointment",
                description="Updates details of an existing appointment.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="AppointmentUpdateInput",
                    description="AppointmentUpdateInput",
                    Fields=[
                        ObjectFieldE(
                            name="startTime",
                            type="datetime",
                            description="The new start time for the appointment, accounting for any time zone considerations.",
                        ),
                        ObjectFieldE(
                            name="endTime",
                            type="datetime",
                            description="The new end time for the appointment, ensuring it follows logically after the start time.",
                        ),
                        ObjectFieldE(
                            name="type",
                            type="str",
                            description="Optionally update the type/category of the appointment.",
                        ),
                        ObjectFieldE(
                            name="status",
                            type="AppointmentStatus",
                            description="The updated status to reflect any changes such as rescheduling or cancellations.",
                        ),
                        ObjectFieldE(
                            name="timeZone",
                            type="str",
                            description="If the time zone needs adjusting to reflect the appropriate scheduling context.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="AppointmentUpdateOutput",
                    description="AppointmentUpdateOutput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="The ID of the appointment that was updated.",
                        ),
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates true if the appointment was successfully updated, false otherwise.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Provides more information about the outcome of the update, such as 'Appointment updated successfully' or 'Update failed due to [reason]'.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="DELETE",
                path="/appointments/{id}",
                function_name="cancel_appointment",
                description="Cancels an existing appointment.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="CancelAppointmentInput",
                    description="CancelAppointmentInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="Unique identifier of the appointment to be canceled.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CancelAppointmentOutput",
                    description="CancelAppointmentOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the appointment cancellation was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A message detailing the outcome of the cancellation request.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="PUT",
                path="/notifications/settings",
                function_name="configure_notifications",
                description="Configures a user's notification preferences.",
                access_level=AccessLevel.USER,
                request_model=ObjectTypeE(
                    name="ConfigureNotificationsRequest",
                    description="ConfigureNotificationsRequest",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="The unique identifier of the user updating their preferences",
                        ),
                        ObjectFieldE(
                            name="emailEnabled",
                            type="bool",
                            description="Indicates whether email notifications are enabled",
                        ),
                        ObjectFieldE(
                            name="emailFrequency",
                            type="str",
                            description="Defines how often email notifications are sent ('immediately', 'daily', 'weekly')",
                        ),
                        ObjectFieldE(
                            name="smsEnabled",
                            type="bool",
                            description="Indicates whether SMS notifications are enabled",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="ConfigureNotificationsResponse",
                    description="ConfigureNotificationsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the update operation was successful",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Provides information about the operation's outcome or failure reason",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/notifications/dispatch",
                function_name="dispatch_notifications",
                description="Sends out notifications based on predefined criteria and user settings.",
                access_level=AccessLevel.ADMIN,
                request_model=ObjectTypeE(
                    name="DispatchNotificationInput",
                    description="DispatchNotificationInput",
                    Fields=[
                        ObjectFieldE(
                            name="criteria",
                            type="str",
                            description="Criteria for notification dispatch, such as 'allPendingWithin24h' to indicate all notifications for appointments occurring in the next 24 hours.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="DispatchNotificationOutput",
                    description="DispatchNotificationOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="If the dispatch was successful overall.",
                        ),
                        ObjectFieldE(
                            name="dispatchedCount",
                            type="int",
                            description="Total number of notifications dispatched.",
                        ),
                        ObjectFieldE(
                            name="failedCount",
                            type="int",
                            description="Number of notifications that failed to dispatch.",
                        ),
                        ObjectFieldE(
                            name="errors",
                            type="[str]",
                            description="List of errors for individual failures, if applicable.",
                        ),
                    ],
                ),
                database_schema=database_schema,
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
                request_model=ObjectTypeE(
                    name="ListInventoryRequest",
                    description="ListInventoryRequest",
                    Fields=[
                        ObjectFieldE(
                            name="filters",
                            type=ObjectTypeE(
                                name="InventoryFilter",
                                description="Optional filters for listing inventory items, including filter by location, batch, and name.",
                                Fields=[
                                    ObjectFieldE(
                                        name="locationId",
                                        type="int",
                                        description="Allows filtering inventory items by their stored location ID.",
                                    ),
                                    ObjectFieldE(
                                        name="batchId",
                                        type="int",
                                        description="Allows filtering inventory items by their associated batch ID.",
                                    ),
                                    ObjectFieldE(
                                        name="name",
                                        type="str",
                                        description="Allows filtering inventory items by a name or partial name match.",
                                    ),
                                ],
                            ),
                            description="Optional filters to apply when listing inventory items.",
                        ),
                        ObjectFieldE(
                            name="pagination",
                            type=ObjectTypeE(
                                name="PaginationParams",
                                description="Parameters for controlling the pagination of the list_inventory response.",
                                Fields=[
                                    ObjectFieldE(
                                        name="page",
                                        type="int",
                                        description="Specifies the page number of inventory items to retrieve.",
                                    ),
                                    ObjectFieldE(
                                        name="pageSize",
                                        type="int",
                                        description="Specifies the number of inventory items per page.",
                                    ),
                                ],
                            ),
                            description="Optional pagination control parameters.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="ListInventoryResponse",
                    description="ListInventoryResponse",
                    Fields=[
                        ObjectFieldE(
                            name="items",
                            type="array[InventoryItem]",
                            description="A list of inventory items that match the request criteria.",
                        ),
                        ObjectFieldE(
                            name="totalItems",
                            type="int",
                            description="The total number of inventory items that match the request filters, ignoring pagination.",
                        ),
                        ObjectFieldE(
                            name="currentPage",
                            type="int",
                            description="The current page number of the inventory items list.",
                        ),
                        ObjectFieldE(
                            name="totalPages",
                            type="int",
                            description="The total number of pages available based on the current filter and pagination settings.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="PUT",
                path="/inventory/{id}",
                function_name="update_inventory_item",
                description="Update an inventory item's details.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="UpdateInventoryItemInput",
                    description="UpdateInventoryItemInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="int",
                            description="the unique identifier of the inventory item to update",
                        ),
                        ObjectFieldE(
                            name="name",
                            type="str",
                            description="optional: the new name of the inventory item",
                        ),
                        ObjectFieldE(
                            name="description",
                            type="str",
                            description="optional: the new description of the inventory item",
                        ),
                        ObjectFieldE(
                            name="quantity",
                            type="int",
                            description="optional: the new quantity of the inventory item",
                        ),
                        ObjectFieldE(
                            name="locationId",
                            type="int",
                            description="optional: the new location identifier where the inventory item is stored",
                        ),
                        ObjectFieldE(
                            name="batchId",
                            type="int",
                            description="optional: the new batch identifier associated with the inventory item",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UpdateInventoryItemOutput",
                    description="UpdateInventoryItemOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="indicates if the update operation was successful",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="provides details on the outcome of the operation, including error messages",
                        ),
                        ObjectFieldE(
                            name="updatedItem",
                            type="InventoryItem",
                            description="optional: the updated inventory item details, provided if the update was successful",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/inventory",
                function_name="create_inventory_item",
                description="Add a new inventory item.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="CreateInventoryItemRequest",
                    description="CreateInventoryItemRequest",
                    Fields=[
                        ObjectFieldE(
                            name="inventoryItem",
                            type=ObjectTypeE(
                                name="InventoryItemCreateInput",
                                description="Defines the necessary parameters for creating a new inventory item, including name, quantity, and optionally description, locationId, and batchId for perishables.",
                                Fields=[
                                    ObjectFieldE(
                                        name="name",
                                        type="str",
                                        description="The name of the inventory item.",
                                    ),
                                    ObjectFieldE(
                                        name="description",
                                        type="str",
                                        description="A brief description of the inventory item. Optional.",
                                    ),
                                    ObjectFieldE(
                                        name="quantity",
                                        type="int",
                                        description="The initial stock quantity of the inventory item.",
                                    ),
                                    ObjectFieldE(
                                        name="locationId",
                                        type="int",
                                        description="The ID of the location where the inventory item is stored. Optional.",
                                    ),
                                    ObjectFieldE(
                                        name="batchId",
                                        type="int",
                                        description="Related batch ID for perishable goods. Optional.",
                                    ),
                                ],
                            ),
                            description="Object containing details necessary for adding a new inventory item.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateInventoryItemResponse",
                    description="CreateInventoryItemResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the item was successfully created.",
                        ),
                        ObjectFieldE(
                            name="itemId",
                            type="int",
                            description="The ID of the newly created inventory item.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A descriptive message about the result of the operation.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="DELETE",
                path="/inventory/{id}",
                function_name="delete_inventory_item",
                description="Remove an inventory item.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="DeleteInventoryItemInput",
                    description="DeleteInventoryItemInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="int",
                            description="The unique identifier of the inventory item to be deleted.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="DeleteInventoryItemOutput",
                    description="DeleteInventoryItemOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the deletion was successful.",
                        ),
                        ObjectFieldE(
                            name="error_message",
                            type="str",
                            description="Provides an error message if the deletion was not successful. This field is optional and may not be present if 'success' is true.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/reports",
                function_name="create_report",
                description="Generate a new report based on provided parameters.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="CreateReportRequest",
                    description="CreateReportRequest",
                    Fields=[
                        ObjectFieldE(
                            name="reportParams",
                            type=ObjectTypeE(
                                name="CreateReportParams",
                                description="Defines the parameters required for creating a new inventory report.",
                                Fields=[
                                    ObjectFieldE(
                                        name="dateRange",
                                        type="DateRange",
                                        description="The date range for which the report should cover.",
                                    ),
                                    ObjectFieldE(
                                        name="reportType",
                                        type="str",
                                        description="Specifies the type of report to generate, such as 'inventoryLevel', 'reordering', or 'expiryTracking'.",
                                    ),
                                    ObjectFieldE(
                                        name="inventoryItems",
                                        type="list[int]",
                                        description="Optional. A list of inventory item IDs to include in the report. If not provided, the report covers all items.",
                                    ),
                                ],
                            ),
                            description="Object containing all necessary parameters to create a report.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateReportResponse",
                    description="CreateReportResponse",
                    Fields=[
                        ObjectFieldE(
                            name="result",
                            type=ObjectTypeE(
                                name="CreateReportResponse",
                                description="The response returned after attempting to create a report. Contains the report's ID if successful.",
                                Fields=[
                                    ObjectFieldE(
                                        name="success",
                                        type="bool",
                                        description="Indicates if the report was successfully created.",
                                    ),
                                    ObjectFieldE(
                                        name="reportId",
                                        type="int",
                                        description="The unique identifier of the newly created report. Null if 'success' is false.",
                                    ),
                                    ObjectFieldE(
                                        name="message",
                                        type="str",
                                        description="A message detailing the outcome of the request.",
                                    ),
                                ],
                            ),
                            description="Object containing the result of the report creation attempt.",
                        )
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/reports",
                function_name="get_reports",
                description="List all available reports.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="GetReportsRequest", description="GetReportsRequest", Fields=[]
                ),
                response_model=ObjectTypeE(
                    name="GetReportsResponse",
                    description="GetReportsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="reports",
                            # type="list[ReportSummary]",
                            type=ObjectTypeE(
                                name="ReportSummary",
                                description="Summarizes essential details of a report for listing purposes.",
                                Fields=[
                                    ObjectFieldE(
                                        name="id",
                                        type="int",
                                        description="Unique identifier of the report",
                                    ),
                                    ObjectFieldE(
                                        name="title",
                                        type="str",
                                        description="Title of the report",
                                    ),
                                    ObjectFieldE(
                                        name="creationDate",
                                        type="datetime",
                                        description="The date and time when the report was created",
                                    ),
                                    ObjectFieldE(
                                        name="description",
                                        type="str",
                                        description="A brief description of the report",
                                    ),
                                ],
                            ),
                            description="A list of report summaries",
                        ),
                        ObjectFieldE(
                            name="totalCount",
                            type="int",
                            description="The total number of reports available",
                        ),
                        ObjectFieldE(
                            name="page",
                            type="int",
                            description="The current page number",
                        ),
                        ObjectFieldE(
                            name="pageSize",
                            type="int",
                            description="The number of items per page",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/integrations",
                function_name="create_integration",
                description="Register a new integration with an external system.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="CreateIntegrationInput",
                    description="CreateIntegrationInput",
                    Fields=[
                        ObjectFieldE(
                            name="systemType",
                            type="str",
                            description="The type of system to integrate.",
                        ),
                        ObjectFieldE(
                            name="details",
                            type="str",
                            description="Configuration details for the integration.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateIntegrationOutput",
                    description="CreateIntegrationOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the operation was successful.",
                        ),
                        ObjectFieldE(
                            name="integrationId",
                            type="int",
                            description="ID of the created integration, if successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Outcome message.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/integrations",
                function_name="list_integrations",
                description="List all external system integrations.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="ListIntegrationsRequest",
                    description="ListIntegrationsRequest",
                    Fields=[],
                ),
                response_model=ObjectTypeE(
                    name="ListIntegrationsResponse",
                    description="ListIntegrationsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="integrations",
                            # type="list[IntegrationSummary]",
                            type=ObjectTypeE(
                                name="IntegrationSummary",
                                description="Summarizes essential details of an external system integration for listing purposes.",
                                Fields=[
                                    ObjectFieldE(
                                        name="id",
                                        type="int",
                                        description="Unique identifier of the integration.",
                                    ),
                                    ObjectFieldE(
                                        name="systemType",
                                        type="str",
                                        description="Type of the external system (e.g., Sales, Procurement).",
                                    ),
                                    ObjectFieldE(
                                        name="details",
                                        type="str",
                                        description="Additional details or description of the integration.",
                                    ),
                                ],
                            ),
                            description="A list of integration summaries detailing the available external system integrations.",
                        )
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/alerts",
                function_name="create_alert",
                description="Set a new alert based on inventory criteria.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="CreateAlertInput",
                    description="CreateAlertInput",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="int",
                            description="The ID of the user setting the alert.",
                        ),
                        ObjectFieldE(
                            name="criteria",
                            type="str",
                            description="Condition or event that triggers the alert.",
                        ),
                        ObjectFieldE(
                            name="threshold",
                            type="int",
                            description="Numeric value that triggers the alert when reached or exceeded.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CreateAlertOutput",
                    description="CreateAlertOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the alert creation was successful.",
                        ),
                        ObjectFieldE(
                            name="alertId",
                            type="int",
                            description="The ID of the newly created alert if successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Descriptive message of the alert creation outcome.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/alerts",
                function_name="list_alerts",
                description="List all configured alerts.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="ListAlertsRequest", description="ListAlertsRequest", Fields=[]
                ),
                response_model=ObjectTypeE(
                    name="ListAlertsResponse",
                    description="ListAlertsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="alerts",
                            type="list[AlertDetail]",
                            description="List containing detailed configurations of all alerts.",
                        )
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/auth/login",
                function_name="user_login",
                description="Authenticate a user and provide token.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="UserLoginInput",
                    description="UserLoginInput",
                    Fields=[
                        ObjectFieldE(
                            name="email",
                            type="str",
                            description="The user's email address.",
                        ),
                        ObjectFieldE(
                            name="password",
                            type="str",
                            description="The user's account password.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UserLoginOutput",
                    description="UserLoginOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="True if the login was successful, false otherwise.",
                        ),
                        ObjectFieldE(
                            name="token",
                            type="str",
                            description="JWT token generated for the session if login is successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Descriptive message about the login attempt.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/auth/logout",
                function_name="user_logout",
                description="Logs out a user, invalidating the session token.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="LogoutInput", description="LogoutInput", Fields=[]
                ),
                response_model=ObjectTypeE(
                    name="LogoutOutput",
                    description="LogoutOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the logout was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Message providing more details on the outcome. It can indicate success or describe why the logout failed.",
                        ),
                    ],
                ),
                database_schema=database_schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/auth/permissions/{userid}",
                function_name="check_permissions",
                description="Verify if a user has permissions for a specific action.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="CheckPermissionsInput",
                    description="CheckPermissionsInput",
                    Fields=[
                        ObjectFieldE(
                            name="userid",
                            type="int",
                            description="The unique identifier of the user.",
                        ),
                        ObjectFieldE(
                            name="action",
                            type="str",
                            description="Specific action or permission to check for. Optional; could be structured to check against multiple actions.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="CheckPermissionsOutput",
                    description="CheckPermissionsOutput",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="int",
                            description="The ID of the user whose permissions were checked.",
                        ),
                        ObjectFieldE(
                            name="permissions",
                            # type="list[PermissionCheckResult]",
                            type=ObjectTypeE(
                                name="PermissionCheckResult",
                                description="Represents the result of checking a user's permissions.",
                                Fields=[
                                    ObjectFieldE(
                                        name="hasPermission",
                                        type="bool",
                                        description="Indicates whether the user has the requested permission.",
                                    ),
                                    ObjectFieldE(
                                        name="message",
                                        type="str",
                                        description="Provides additional information about the permission check, e.g., granted, denied, or reason for denial.",
                                    ),
                                ],
                            ),
                            description="A list of results for each action's permission check.",
                        ),
                    ],
                ),
                database_schema=database_schema,
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
                request_model=ObjectTypeE(
                    name="InvoiceCreationRequest",
                    description="InvoiceCreationRequest",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="Identifier for the user who is creating the invoice.",
                        ),
                        ObjectFieldE(
                            name="items",
                            # type="list[InvoiceItemInput]",
                            type=ObjectTypeE(
                                name="InvoiceItemInput",
                                description="Details for each item included in the invoice.",
                                Fields=[
                                    ObjectFieldE(
                                        name="description",
                                        type="str",
                                        description="Description of the line item.",
                                    ),
                                    ObjectFieldE(
                                        name="quantity",
                                        type="int",
                                        description="Quantity of the line item.",
                                    ),
                                    ObjectFieldE(
                                        name="price",
                                        type="float",
                                        description="Price per unit of the line item.",
                                    ),
                                ],
                            ),
                            description="Array of line items to be included in the invoice.",
                        ),
                        ObjectFieldE(
                            name="currency",
                            type="str",
                            description="Currency in which the invoice is being issued.",
                        ),
                        ObjectFieldE(
                            name="taxRate",
                            type="float",
                            description="Tax rate applicable to the invoice, represented as a percentage.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="InvoiceCreationResponse",
                    description="InvoiceCreationResponse",
                    Fields=[
                        ObjectFieldE(
                            name="invoiceId",
                            type="str",
                            description="Unique identifier for the newly created invoice.",
                        ),
                        ObjectFieldE(
                            name="status",
                            type="str",
                            description="Status of the invoice after creation. Expected values are 'Draft' or 'Finalized'.",
                        ),
                        ObjectFieldE(
                            name="creationDate",
                            type="datetime",
                            description="Timestamp reflecting when the invoice was created.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/invoices/{id}",
                function_name="edit_invoice",
                description="Edits an existing invoice by ID.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="EditInvoiceInput",
                    description="EditInvoiceInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="The unique identifier of the invoice to be edited.",
                        ),
                        ObjectFieldE(
                            name="invoiceDetails",
                            type=ObjectTypeE(
                                name="InvoiceEditModel",
                                description="Model for editing invoice details, allowing updates to various invoice fields while ensuring that changes to critical fields like currency or finalized status are handled with caution.",
                                Fields=[
                                    ObjectFieldE(
                                        name="status",
                                        type="Optional[str]",
                                        description="Allows modifying the status of the invoice, i.e., from draft to finalized, but with strict checks to prevent arbitrary status changes.",
                                    ),
                                    ObjectFieldE(
                                        name="items",
                                        # type="Optional[Array[ItemEditModel]]",
                                        type=ObjectTypeE(
                                            name="ItemEditModel",
                                            description="Model for adding or editing line items within an invoice.",
                                            Fields=[
                                                ObjectFieldE(
                                                    name="description",
                                                    type="str",
                                                    description="Description of the invoice item.",
                                                ),
                                                ObjectFieldE(
                                                    name="quantity",
                                                    type="int",
                                                    description="Quantity of the item.",
                                                ),
                                                ObjectFieldE(
                                                    name="price",
                                                    type="float",
                                                    description="Price per unit of the item.",
                                                ),
                                                ObjectFieldE(
                                                    name="id",
                                                    type="String (Optional)",
                                                    description="Unique ID of the item if it exists. If provided, the item will be updated; otherwise, a new item will be added.",
                                                ),
                                            ],
                                        ),
                                        description="List of line items to be added or updated in the invoice. Each item modification is described in a separate model.",
                                    ),
                                    ObjectFieldE(
                                        name="currency",
                                        type="Optional[str]",
                                        description="Currency in which the invoice is denoted. Modifications should ensure no discrepancies in already entered amounts.",
                                    ),
                                ],
                            ),
                            description="The details of the invoice to be edited, encapsulated within the InvoiceEditModel.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="EditInvoiceOutput",
                    description="EditInvoiceOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the edit operation was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A message describing the result of the operation, particularly useful in case of failure.",
                        ),
                        ObjectFieldE(
                            name="updatedInvoice",
                            type="Invoice",
                            description="The updated invoice object reflecting the changes made. Null if operation failed.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/invoices/{id}",
                function_name="get_invoice",
                description="Retrieves invoice details by ID.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="GetInvoiceInput",
                    description="GetInvoiceInput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="The unique ID of the invoice to retrieve.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="GetInvoiceOutput",
                    description="GetInvoiceOutput",
                    Fields=[
                        ObjectFieldE(
                            name="id",
                            type="str",
                            description="The unique ID of the invoice.",
                        ),
                        ObjectFieldE(
                            name="number",
                            type="str",
                            description="The unique invoice number.",
                        ),
                        ObjectFieldE(
                            name="status",
                            type="str",
                            description="Current status of the invoice (e.g., draft, finalized).",
                        ),
                        ObjectFieldE(
                            name="items",
                            type="array of InvoiceItem",
                            description="A collection of line items associated with the invoice. Each item contains details such as description, quantity, and price.",
                        ),
                        ObjectFieldE(
                            name="payment",
                            type="Payment or null",
                            description="Payment details associated with this invoice. Null if no payment has been made yet.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/invoices",
                function_name="list_invoices",
                description="Lists all invoices related to a user.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="ListInvoicesRequest",
                    description="ListInvoicesRequest",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="The unique identifier of the user whose invoices are to be listed.",
                        ),
                        ObjectFieldE(
                            name="page",
                            type="int",
                            description="Pagination ObjectFieldE, denotes the page number of the invoice list to be retrieved.",
                        ),
                        ObjectFieldE(
                            name="pageSize",
                            type="int",
                            description="Pagination ObjectFieldE, denotes the number of invoices to be listed per page.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="ListInvoicesResponse",
                    description="ListInvoicesResponse",
                    Fields=[
                        ObjectFieldE(
                            name="invoices",
                            # type="list[InvoiceSummary]",
                            type=ObjectTypeE(
                                name="InvoiceSummary",
                                description="A concise model representing the key information of an invoice for listing purposes.",
                                Fields=[
                                    ObjectFieldE(
                                        name="invoiceId",
                                        type="str",
                                        description="Unique identifier for the invoice.",
                                    ),
                                    ObjectFieldE(
                                        name="invoiceNumber",
                                        type="str",
                                        description="The unique number associated with the invoice.",
                                    ),
                                    ObjectFieldE(
                                        name="status",
                                        type="str",
                                        description="Current status of the invoice (e.g., draft, finalized).",
                                    ),
                                    ObjectFieldE(
                                        name="totalAmount",
                                        type="float",
                                        description="Total amount of the invoice, taking into account item prices and quantities.",
                                    ),
                                    ObjectFieldE(
                                        name="currency",
                                        type="str",
                                        description="The currency in which the invoice was issued.",
                                    ),
                                    ObjectFieldE(
                                        name="createdAt",
                                        type="datetime",
                                        description="The date and time when the invoice was created.",
                                    ),
                                ],
                            ),
                            description="An array of invoice summary objects.",
                        ),
                        ObjectFieldE(
                            name="total",
                            type="int",
                            description="Total number of invoices available for the user.",
                        ),
                        ObjectFieldE(
                            name="currentPage",
                            type="int",
                            description="The current page number being returned in the response.",
                        ),
                        ObjectFieldE(
                            name="pageSize",
                            type="int",
                            description="The number of invoices returned per page.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/payments/initiate/{invoiceId}",
                function_name="initiate_payment",
                description="Initiates a payment for an invoice.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="PaymentInitiationRequest",
                    description="PaymentInitiationRequest",
                    Fields=[
                        ObjectFieldE(
                            name="invoiceId",
                            type="str",
                            description="Unique ID of the invoice for which the payment is being initiated.",
                        ),
                        ObjectFieldE(
                            name="gatewayId",
                            type="str",
                            description="Identifier of the payment gateway through which the payment will be processed.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="PaymentInitiationResponse",
                    description="PaymentInitiationResponse",
                    Fields=[
                        ObjectFieldE(
                            name="paymentId",
                            type="str",
                            description="Unique identifier for the payment transaction, provided by the system.",
                        ),
                        ObjectFieldE(
                            name="status",
                            type="str",
                            description="Status of the payment initiation, which could be 'Pending', 'Failed', or other relevant terms.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/payments/confirm/{paymentId}",
                function_name="confirm_payment",
                description="Confirms a payment has been completed.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="PaymentConfirmationRequest",
                    description="PaymentConfirmationRequest",
                    Fields=[
                        ObjectFieldE(
                            name="paymentId",
                            type="str",
                            description="The unique identifier of the payment to be confirmed.",
                        ),
                        ObjectFieldE(
                            name="confirmationStatus",
                            type="str",
                            description="Indicates the status of the payment confirmation attempt.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="PaymentConfirmationResponse",
                    description="PaymentConfirmationResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Boolean flag indicating if the payment confirmation was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A message providing more details on the confirmation status.",
                        ),
                        ObjectFieldE(
                            name="updatedPaymentDetails",
                            type="Payment",
                            description="The updated payment details post-confirmation attempt, reflecting the new status and any additional updates.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/notifications/remind",
                function_name="send_reminder",
                description="Sends a reminder for an unpaid invoice.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="ReminderNotificationInput",
                    description="ReminderNotificationInput",
                    Fields=[
                        ObjectFieldE(
                            name="invoiceId",
                            type="str",
                            description="Unique identifier for the invoice the reminder pertains to.",
                        ),
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="Unique identifier for the user associated with the invoice to send the notification to.",
                        ),
                        ObjectFieldE(
                            name="medium",
                            type="str",
                            description="Preferred medium of notification (e.g., Email, SMS).",
                        ),
                        ObjectFieldE(
                            name="sendTime",
                            type="datetime",
                            description="Scheduled time for sending the reminder.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="ReminderNotificationOutput",
                    description="ReminderNotificationOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the reminder was successfully sent.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A descriptive message about the outcome of the attempt.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/reports/generate",
                function_name="generate_report",
                description="Generates a financial report based on specified parameters.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="GenerateReportInput",
                    description="GenerateReportInput",
                    Fields=[
                        ObjectFieldE(
                            name="userId",
                            type="str",
                            description="The user's ID for whom the report is being generated.",
                        ),
                        ObjectFieldE(
                            name="reportType",
                            type="str",
                            description="Specifies the type of financial report required.",
                        ),
                        ObjectFieldE(
                            name="startDate",
                            type="datetime",
                            description="The start date for the reporting period.",
                        ),
                        ObjectFieldE(
                            name="endDate",
                            type="datetime",
                            description="The end date for the reporting period.",
                        ),
                        ObjectFieldE(
                            name="filters",
                            type="list[str]",
                            description="Optional filters to refine the report data.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="GenerateReportOutput",
                    description="GenerateReportOutput",
                    Fields=[
                        ObjectFieldE(
                            name="report",
                            type=ObjectTypeE(
                                name="FinancialReport",
                                description="Represents the structured output of a financial report, including various metrics and insights.",
                                Fields=[
                                    ObjectFieldE(
                                        name="reportType",
                                        type="str",
                                        description="Type of the generated report.",
                                    ),
                                    ObjectFieldE(
                                        name="generatedAt",
                                        type="datetime",
                                        description="Timestamp of when the report was generated.",
                                    ),
                                    ObjectFieldE(
                                        name="metrics",
                                        # type="List[ReportMetric]",
                                        type=ObjectTypeE(
                                            name="ReportMetric",
                                            description="Details of a single metric within the financial report.",
                                            Fields=[
                                                ObjectFieldE(
                                                    name="metricName",
                                                    type="str",
                                                    description="Name of the metric.",
                                                ),
                                                ObjectFieldE(
                                                    name="value",
                                                    type="float",
                                                    description="Quantitative value of the metric.",
                                                ),
                                                ObjectFieldE(
                                                    name="unit",
                                                    type="str",
                                                    description="Unit of measurement for the metric.",
                                                ),
                                                ObjectFieldE(
                                                    name="description",
                                                    type="str",
                                                    description="A brief description or insight related to the metric.",
                                                ),
                                            ],
                                        ),
                                        description="A collection of metrics included in the report.",
                                    ),
                                    ObjectFieldE(
                                        name="insights",
                                        type="List[str]",
                                        description="List of insights derived from the report data.",
                                    ),
                                ],
                            ),
                            description="The detailed financial report generated based on the input parameters.",
                        )
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="GET",
                path="/insights",
                function_name="fetch_insights",
                description="Provides strategic financial insights.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="FinancialInsightsRequest",
                    description="FinancialInsightsRequest",
                    Fields=[
                        ObjectFieldE(
                            name="startDate",
                            type="datetime",
                            description="The start date for the range of financial data to consider.",
                        ),
                        ObjectFieldE(
                            name="endDate",
                            type="datetime",
                            description="The end date for the range of financial data to consider.",
                        ),
                        ObjectFieldE(
                            name="metrics",
                            type="list[str]",
                            description="Optional. A list of specific financial metrics to retrieve insights for.",
                        ),
                    ],
                ),
                response_model=ObjectTypeE(
                    name="FinancialInsightsResponse",
                    description="FinancialInsightsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="insights",
                            # type="list[FinancialInsight]",
                            type=ObjectTypeE(
                                name="FinancialInsight",
                                description="Represents a high-level financial insight derived from aggregating financial data.",
                                Fields=[
                                    ObjectFieldE(
                                        name="label",
                                        type="str",
                                        description="The name of the financial insight or metric.",
                                    ),
                                    ObjectFieldE(
                                        name="value",
                                        type="float",
                                        description="The numerical value of the insight.",
                                    ),
                                    ObjectFieldE(
                                        name="trend",
                                        type="str",
                                        description="Indicates the trend of this metric (e.g., 'increasing', 'decreasing', 'stable').",
                                    ),
                                    ObjectFieldE(
                                        name="interpretation",
                                        type="str",
                                        description="A brief expert analysis or interpretation of what this insight suggests about the business's financial health.",
                                    ),
                                ],
                            ),
                            description="A collection of financial insights.",
                        )
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="PATCH",
                path="/security/settings",
                function_name="update_security_settings",
                description="Updates security settings and protocols.",
                access_level=AccessLevel.ADMIN,
                request_model=ObjectTypeE(
                    name="UpdateSecuritySettingsRequest",
                    description="UpdateSecuritySettingsRequest",
                    Fields=[
                        ObjectFieldE(
                            name="updates",
                            # type="list[SecuritySettingUpdate]",
                            type=ObjectTypeE(
                                name="SecuritySettingUpdate",
                                description="Represents a security setting that needs to be updated.",
                                Fields=[
                                    ObjectFieldE(
                                        name="settingName",
                                        type="str",
                                        description="The name of the security setting to update.",
                                    ),
                                    ObjectFieldE(
                                        name="newValue",
                                        type="str",
                                        description="The new value for the security setting.",
                                    ),
                                ],
                            ),
                            description="A list of security settings to update, each indicating the setting name and its new value.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="UpdateSecuritySettingsResponse",
                    description="UpdateSecuritySettingsResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the update operation was successful.",
                        ),
                        ObjectFieldE(
                            name="updatedSettings",
                            # type="list[SecuritySettingUpdate]",
                            type=ObjectTypeE(
                                name="SecuritySettingUpdate",
                                description="Represents a security setting that needs to be updated.",
                                Fields=[
                                    ObjectFieldE(
                                        name="settingName",
                                        type="str",
                                        description="The name of the security setting to update.",
                                    ),
                                    ObjectFieldE(
                                        name="newValue",
                                        type="str",
                                        description="The new value for the security setting.",
                                    ),
                                ],
                            ),
                            description="A list of all settings that were successfully updated.",
                        ),
                        ObjectFieldE(
                            name="failedSettings",
                            # type="list[SecuritySettingUpdate]",
                            type=ObjectTypeE(
                                name="SecuritySettingUpdate",
                                description="Represents a security setting that needs to be updated.",
                                Fields=[
                                    ObjectFieldE(
                                        name="settingName",
                                        type="str",
                                        description="The name of the security setting to update.",
                                    ),
                                    ObjectFieldE(
                                        name="newValue",
                                        type="str",
                                        description="The new value for the security setting.",
                                    ),
                                ],
                            ),
                            description="A list of settings that failed to update, with descriptions of the failure reasons.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/compliance/logs",
                function_name="log_compliance_action",
                description="Records a compliance-related action for auditing.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="LogComplianceActionInput",
                    description="LogComplianceActionInput",
                    Fields=[
                        ObjectFieldE(
                            name="complianceAction",
                            type=ObjectTypeE(
                                name="ComplianceAction",
                                description="Represents a compliance-related action that needs to be logged for auditing.",
                                Fields=[
                                    ObjectFieldE(
                                        name="actionType",
                                        type="str",
                                        description="The type of action performed, e.g., 'Data Update', 'View Sensitive Information', etc.",
                                    ),
                                    ObjectFieldE(
                                        name="description",
                                        type="str",
                                        description="A detailed description of the action performed.",
                                    ),
                                    ObjectFieldE(
                                        name="performedBy",
                                        type="str",
                                        description="Identifier for the user or system component that performed the action.",
                                    ),
                                    ObjectFieldE(
                                        name="timestamp",
                                        type="datetime",
                                        description="Timestamp when the action was performed.",
                                    ),
                                ],
                            ),
                            description="The compliance action that needs to be logged.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="LogComplianceActionOutput",
                    description="LogComplianceActionOutput",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates whether the logging was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="A descriptive message regarding the outcome of the log attempt.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
            APIRouteRequirement(
                method="POST",
                path="/integration/payment-gateway",
                function_name="connect_payment_gateway",
                description="Sets up connection with a specified payment gateway.",
                access_level=AccessLevel.PUBLIC,
                request_model=ObjectTypeE(
                    name="PaymentGatewayConnectionRequest",
                    description="PaymentGatewayConnectionRequest",
                    Fields=[
                        ObjectFieldE(
                            name="connectionDetails",
                            type=ObjectTypeE(
                                name="PaymentGatewayConnectionInput",
                                description="Data required to initiate a connection with a payment gateway.",
                                Fields=[
                                    ObjectFieldE(
                                        name="gatewayName",
                                        type="str",
                                        description="The name of the payment gateway to connect.",
                                    ),
                                    ObjectFieldE(
                                        name="apiKey",
                                        type="str",
                                        description="The API key provided by the payment gateway for authentication.",
                                    ),
                                    ObjectFieldE(
                                        name="apiSecret",
                                        type="str",
                                        description="The API secret or other credentials required for secure access.",
                                    ),
                                ],
                            ),
                            description="An object holding the necessary connection details.",
                        )
                    ],
                ),
                response_model=ObjectTypeE(
                    name="PaymentGatewayConnectionResponse",
                    description="PaymentGatewayConnectionResponse",
                    Fields=[
                        ObjectFieldE(
                            name="success",
                            type="bool",
                            description="Indicates if the connection attempt was successful.",
                        ),
                        ObjectFieldE(
                            name="message",
                            type="str",
                            description="Provides more detail on the connection status, including errors if any.",
                        ),
                        ObjectFieldE(
                            name="gatewayId",
                            type="Optional[str]",
                            description="The unique identifier for the gateway in the system, provided upon a successful connection.",
                        ),
                    ],
                ),
                database_schema=schema,
            ),
        ],
    )


def tictactoe_game_requirements() -> ApplicationRequirements:
    request = ObjectTypeE(
        name="TurnRequest",
        description="A request to make a move in the tictactoe game.",
        Fields=[
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

    response = ObjectTypeE(
        name="GameStateResponse",
        description="A response containing the current state of the game.",
        Fields=[
            ObjectFieldE(
                name="gameId",
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
    logger.info(calendar_booking_system())
    logger.info(inventory_mgmt_system())
    logger.info(invoice_payment_tracking())
