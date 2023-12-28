from codex.model import InputParameter, Node, OutputParameter

registration_path = [
    # Node for requesting user registration details
    Node(  # type: ignore
        description="Takes in user details for registration",
        name="request_registration",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="str",
                name="username",
                description="Username for the new user",
            ),
            OutputParameter(
                param_type="str",
                name="password",
                description="Password for the new user",
            ),
            OutputParameter(
                param_type="str", name="email", description="Email of the new user"
            ),
        ],
        package_requirements=[],
    ),
    # Node for registering a new user
    Node(  # type: ignore
        description="Registers a new user in the system",
        name="register_user",
        input_params=[
            InputParameter(
                param_type="str",
                name="username",
                description="Username for the new user",
            ),
            InputParameter(
                param_type="str",
                name="password",
                description="Password for the new user",
            ),
            InputParameter(
                param_type="str", name="email", description="Email of the new user"
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="registration_success",
                description="Indicates if the registration was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after registration
    Node(  # type: ignore
        name="response_registration",
        description="Returns the result of the registration process",
        input_params=[
            InputParameter(
                param_type="bool",
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
    Node(  # type: ignore
        description="Takes in user login details",
        name="request_login",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="str", name="username", description="Username of the user"
            ),
            OutputParameter(
                param_type="str", name="password", description="Password of the user"
            ),
        ],
        package_requirements=[],
    ),
    # Node for authenticating user
    Node(  # type: ignore
        description="Authenticates the user credentials",
        name="authenticate_user",
        input_params=[
            InputParameter(
                param_type="str", name="username", description="Username of the user"
            ),
            InputParameter(
                param_type="str", name="password", description="Password of the user"
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="login_success",
                description="Indicates if the login was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after login
    Node(  # type: ignore
        name="response_login",
        description="Returns the result of the login process",
        input_params=[
            InputParameter(
                param_type="bool",
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
    Node(  # type: ignore
        description="Takes in details for creating a new post",
        name="request_create_post",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="str", name="title", description="Title of the post"
            ),
            OutputParameter(
                param_type="str", name="content", description="Content of the post"
            ),
        ],
        package_requirements=[],
    ),
    # Node for creating a new post
    Node(  # type: ignore
        description="Creates a new post",
        name="create_post",
        input_params=[
            InputParameter(
                param_type="str", name="title", description="Title of the post"
            ),
            InputParameter(
                param_type="str", name="content", description="Content of the post"
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="post_creation_success",
                description="Indicates if the post creation was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post creation
    Node(  # type: ignore
        name="response_create_post",
        description="Returns the result of the post creation process",
        input_params=[
            InputParameter(
                param_type="bool",
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
    Node(  # type: ignore
        description="Takes in details for editing an existing post",
        name="request_edit_post",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="int", name="post_id", description="ID of the post to edit"
            ),
            OutputParameter(
                param_type="str",
                name="new_title",
                description="New title of the post, if any",
            ),
            OutputParameter(
                param_type="str",
                name="new_content",
                description="New content of the post, if any",
            ),
        ],
        package_requirements=[],
    ),
    # Node for editing an existing post
    Node(  # type: ignore
        description="Edits an existing post",
        name="edit_post",
        input_params=[
            InputParameter(
                param_type="int", name="post_id", description="ID of the post to edit"
            ),
            InputParameter(
                param_type="str",
                name="new_title",
                description="New title of the post, if any",
            ),
            InputParameter(
                param_type="str",
                name="new_content",
                description="New content of the post, if any",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="post_edit_success",
                description="Indicates if the post edit was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post edit
    Node(  # type: ignore
        name="response_edit_post",
        description="Returns the result of the post editing process",
        input_params=[
            InputParameter(
                param_type="bool",
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
    Node(  # type: ignore
        description="Takes in details for deleting an existing post",
        name="request_delete_post",
        input_params=None,
        output_params=[
            OutputParameter(
                param_type="int", name="post_id", description="ID of the post to delete"
            ),
        ],
        package_requirements=[],
    ),
    # Node for deleting an existing post
    Node(  # type: ignore
        description="Deletes an existing post",
        name="delete_post",
        input_params=[
            InputParameter(
                param_type="int", name="post_id", description="ID of the post to delete"
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="post_delete_success",
                description="Indicates if the post deletion was successful",
            ),
        ],
        package_requirements=[],
    ),
    # Node for sending response after post deletion
    Node(  # type: ignore
        name="response_delete_post",
        description="Returns the result of the post deletion process",
        input_params=[
            InputParameter(
                param_type="bool",
                name="post_delete_success",
                description="Indicates if the post deletion was successful",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]
