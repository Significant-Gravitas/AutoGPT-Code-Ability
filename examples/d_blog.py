from codex.model import Node, Parameter

registration_path = [
    # Node for requesting user registration details
    Node(
        description="Takes in user details for registration",
        name="request_registration",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="str",
                name="username",
                description="Username for the new user",
            ),
            Parameter(
                prama_type="str",
                name="password",
                description="Password for the new user",
            ),
            Parameter(
                prama_type="str", name="email", description="Email of the new user"
            ),
        ],
        package_requirements=[],
    ),
    # Node for registering a new user
    Node(
        description="Registers a new user in the system",
        name="register_user",
        input_params=[
            Parameter(
                prama_type="str",
                name="username",
                description="Username for the new user",
            ),
            Parameter(
                prama_type="str",
                name="password",
                description="Password for the new user",
            ),
            Parameter(
                prama_type="str", name="email", description="Email of the new user"
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="registration_success",
                description="Indicates if the registration was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after registration
    Node(
        name="response_registration",
        description="Returns the result of the registration process",
        input_params=[
            Parameter(
                prama_type="bool",
                name="registration_success",
                description="Indicates if the registration was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]

login_path = [
    # Node for requesting login details
    Node(
        description="Takes in user login details",
        name="request_login",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="str", name="username", description="Username of the user"
            ),
            Parameter(
                prama_type="str", name="password", description="Password of the user"
            ),
        ],
        package_requirements=[],
    ),
    # Node for authenticating user
    Node(
        description="Authenticates the user credentials",
        name="authenticate_user",
        input_params=[
            Parameter(
                prama_type="str", name="username", description="Username of the user"
            ),
            Parameter(
                prama_type="str", name="password", description="Password of the user"
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="login_success",
                description="Indicates if the login was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after login
    Node(
        name="response_login",
        description="Returns the result of the login process",
        input_params=[
            Parameter(
                prama_type="bool",
                name="login_success",
                description="Indicates if the login was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]

create_post_path = [
    # Node for requesting post creation details
    Node(
        description="Takes in details for creating a new post",
        name="request_create_post",
        input_params=None,
        output_params=[
            Parameter(prama_type="str", name="title", description="Title of the post"),
            Parameter(
                prama_type="str", name="content", description="Content of the post"
            ),
        ],
        package_requirements=[],
    ),
    # Node for creating a new post
    Node(
        description="Creates a new post",
        name="create_post",
        input_params=[
            Parameter(prama_type="str", name="title", description="Title of the post"),
            Parameter(
                prama_type="str", name="content", description="Content of the post"
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="post_creation_success",
                description="Indicates if the post creation was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post creation
    Node(
        name="response_create_post",
        description="Returns the result of the post creation process",
        input_params=[
            Parameter(
                prama_type="bool",
                name="post_creation_success",
                description="Indicates if the post creation was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]

edit_post_path = [
    # Node for requesting post editing details
    Node(
        description="Takes in details for editing an existing post",
        name="request_edit_post",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="int", name="post_id", description="ID of the post to edit"
            ),
            Parameter(
                prama_type="str",
                name="new_title",
                description="New title of the post, if any",
            ),
            Parameter(
                prama_type="str",
                name="new_content",
                description="New content of the post, if any",
            ),
        ],
        package_requirements=[],
    ),
    # Node for editing an existing post
    Node(
        description="Edits an existing post",
        name="edit_post",
        input_params=[
            Parameter(
                prama_type="int", name="post_id", description="ID of the post to edit"
            ),
            Parameter(
                prama_type="str",
                name="new_title",
                description="New title of the post, if any",
            ),
            Parameter(
                prama_type="str",
                name="new_content",
                description="New content of the post, if any",
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="post_edit_success",
                description="Indicates if the post edit was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post edit
    Node(
        name="response_edit_post",
        description="Returns the result of the post editing process",
        input_params=[
            Parameter(
                prama_type="bool",
                name="post_edit_success",
                description="Indicates if the post edit was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]

delete_post_path = [
    # Node for requesting post deletion
    Node(
        description="Takes in details for deleting an existing post",
        name="request_delete_post",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="int", name="post_id", description="ID of the post to delete"
            ),
        ],
        package_requirements=[],
    ),
    # Node for deleting an existing post
    Node(
        description="Deletes an existing post",
        name="delete_post",
        input_params=[
            Parameter(
                prama_type="int", name="post_id", description="ID of the post to delete"
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="post_delete_success",
                description="Indicates if the post deletion was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post deletion
    Node(
        name="response_delete_post",
        description="Returns the result of the post deletion process",
        input_params=[
            Parameter(
                prama_type="bool",
                name="post_delete_success",
                description="Indicates if the post deletion was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]
