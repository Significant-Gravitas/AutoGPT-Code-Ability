from codex.model import InputParameter, Node, OutputParameter

# Nodes for User Registration Process
registration_nodes = [
    Node(  # type: ignore
        description="Receives user registration details",
        name="request_node",
        output_params=[
            OutputParameter(
                param_type="str",
                name="username",
                description="The username of the new user",
            ),
            OutputParameter(
                param_type="str",
                name="password",
                description="The password for the new user",
            ),
            OutputParameter(
                param_type="str",
                name="email",
                description="The email address of the new user",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Validates the provided user data",
        name="validate_user_data",
        input_params=[
            InputParameter(
                param_type="str",
                name="username",
                description="The username of the new user",
            ),
            InputParameter(
                param_type="str",
                name="password",
                description="The password for the new user",
            ),
            InputParameter(
                param_type="str",
                name="email",
                description="The email address of the new user",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="is_valid",
                description="Indicates if the user data is valid",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if validation fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Registers the new user in the system",
        name="register_user",
        input_params=[
            InputParameter(
                param_type="str",
                name="username",
                description="The username of the new user",
            ),
            InputParameter(
                param_type="str",
                name="password",
                description="The password for the new user",
            ),
            InputParameter(
                param_type="str",
                name="email",
                description="The email address of the new user",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="registration_success",
                description="Indicates if the registration was successful",
            ),
            OutputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the new user",
                optional=True,
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if registration fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Returns success or error message",
        name="response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="registration_success",
                description="Indicates if the registration was successful",
            ),
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the new user",
                optional=True,
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if registration fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for User Login Process
login_nodes = [
    Node(  # type: ignore
        description="Receives user login credentials",
        name="login_request_node",
        input_params=None,
        output_params=[
            InputParameter(
                param_type="str",
                name="username",
                description="The username of the user",
            ),
            InputParameter(
                param_type="str",
                name="password",
                description="The password of the user",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Authenticates the user credentials",
        name="authenticate_user",
        input_params=[
            InputParameter(
                param_type="str",
                name="username",
                description="The username of the user",
            ),
            InputParameter(
                param_type="str",
                name="password",
                description="The password of the user",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="authentication_success",
                description="Indicates if the authentication was successful",
            ),
            OutputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user",
                optional=True,
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if authentication fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Returns a success message with user data or an error message",
        name="login_response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="authentication_success",
                description="Indicates if the authentication was successful",
            ),
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user",
                optional=True,
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if authentication fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for Send Message Process
send_message_nodes = [
    Node(  # type: ignore
        description="Receives message data including sender, receiver,"
        " and message content",
        name="message_request_node",
        input_params=None,
        output_params=[
            InputParameter(
                param_type="str",
                name="sender_id",
                description="The unique identifier for the sender",
            ),
            InputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            InputParameter(
                param_type="str",
                name="message_content",
                description="The content of the message",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Validates the message content and the receiver's existence",
        name="validate_message",
        input_params=[
            InputParameter(
                param_type="str",
                name="sender_id",
                description="The unique identifier for the sender",
            ),
            InputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            InputParameter(
                param_type="str",
                name="message_content",
                description="The content of the message",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="validation_success",
                description="Indicates if the message validation was successful",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if validation fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Stores the message in the database",
        name="store_message",
        input_params=[
            InputParameter(
                param_type="str",
                name="sender_id",
                description="The unique identifier for the sender",
            ),
            InputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            InputParameter(
                param_type="str",
                name="message_content",
                description="The content of the message",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="storage_success",
                description="Indicates if the message was successfully stored",
            ),
            OutputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the stored message",
                optional=True,
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if storage fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Sends a notification to the receiver",
        name="notify_receiver",
        input_params=[
            InputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            InputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the stored message",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification was successfully sent",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if notification fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Returns a confirmation that the message was sent",
        name="message_response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification was successfully sent",
            ),
            InputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the stored message",
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if notification fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for Receive Messages Process
receive_message_nodes = [
    Node(  # type: ignore
        description="Requests new messages for a user",
        name="message_fetch_request_node",
        input_params=None,
        output_params=[
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user requesting messages",
            )
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Retrieves new messages from the database",
        name="fetch_messages",
        input_params=[
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user requesting messages",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="List[str]",
                name="messages",
                description="List of new messages",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if message retrieval fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Returns a list of new messages",
        name="message_fetch_response_node",
        input_params=[
            InputParameter(
                param_type="List[str]",
                name="messages",
                description="List of new messages",
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if message retrieval fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for User Presence Update Process
user_presence_nodes = [
    Node(  # type: ignore
        description="Receives a signal when a user becomes active or inactive",
        name="presence_update_request_node",
        input_params=None,
        output_params=[
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user",
            ),
            InputParameter(
                param_type="bool",
                name="is_active",
                description="Indicates if the user is active",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Updates the user's presence status in the system",
        name="update_presence_status",
        input_params=[
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user",
            ),
            InputParameter(
                param_type="bool",
                name="is_active",
                description="Indicates if the user is active",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="update_success",
                description="Indicates if the presence status update was successful",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if the update fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Notifies the user's contacts about the presence status change",
        name="notify_contacts_presence_change",
        input_params=[
            InputParameter(
                param_type="str",
                name="user_id",
                description="The unique identifier for the user",
            ),
            InputParameter(
                param_type="bool",
                name="is_active",
                description="Indicates if the user is active",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification to contacts was successful",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if notification fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Acknowledges the update of user presence",
        name="presence_update_response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="update_success",
                description="Indicates if the presence status update was successful",
            ),
            InputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification to contacts was successful",
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if either update or notification fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for Typing Indicator Process
typing_indicator_nodes = [
    Node(  # type: ignore
        description="Receives typing status from the sender",
        name="typing_status_request_node",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="str",
                name="sender_id",
                description="The unique identifier for the sender",
            ),
            OutputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            OutputParameter(
                param_type="bool",
                name="is_typing",
                description="Indicates if the sender is typing",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Broadcasts the typing status to the receiver",
        name="broadcast_typing_status",
        input_params=[
            InputParameter(
                param_type="str",
                name="sender_id",
                description="The unique identifier for the sender",
            ),
            InputParameter(
                param_type="str",
                name="receiver_id",
                description="The unique identifier for the receiver",
            ),
            InputParameter(
                param_type="bool",
                name="is_typing",
                description="Indicates if the sender is typing",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="broadcast_success",
                description="Indicates if the typing status was"
                " successfully broadcasted",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if broadcasting fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Acknowledges the status broadcast",
        name="typing_status_response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="broadcast_success",
                description="Indicates if the typing status was"
                " successfully broadcasted",
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if broadcasting fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]

# Nodes for Read Receipts Process
read_receipts_nodes = [
    Node(  # type: ignore
        description="Receives read confirmation for a message",
        name="read_receipt_request_node",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the message being read",
            ),
            OutputParameter(
                param_type="str",
                name="reader_id",
                description="The unique identifier for the reader of the message",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Updates the read status of the message",
        name="update_read_status",
        input_params=[
            InputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the message being read",
            ),
            InputParameter(
                param_type="str",
                name="reader_id",
                description="The unique identifier for the reader of the message",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="update_success",
                description="Indicates if the read status update was successful",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if the update fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Notifies the sender that the message has been read",
        name="notify_sender_read_receipt",
        input_params=[
            InputParameter(
                param_type="str",
                name="message_id",
                description="The unique identifier for the message being read",
            ),
            InputParameter(
                param_type="str",
                name="reader_id",
                description="The unique identifier for the reader of the message",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification to the"
                "sender was successful",
            ),
            OutputParameter(
                param_type="str",
                name="error_message",
                description="Error message if notification fails",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Acknowledges the read receipt update",
        name="read_receipt_response_node",
        input_params=[
            InputParameter(
                param_type="bool",
                name="update_success",
                description="Indicates if the read status update was successful",
            ),
            InputParameter(
                param_type="bool",
                name="notification_success",
                description="Indicates if the notification to "
                "the sender was successful",
            ),
            InputParameter(
                param_type="str",
                name="error_message",
                description="Error message if either update or notification fails",
                optional=True,
            ),
        ],
        output_params=None,
        package_requirements=[],
    ),
]
