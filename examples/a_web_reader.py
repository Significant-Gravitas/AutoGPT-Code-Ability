from codex.model import InputParameter, Node, OutputParameter

nodes = [
    Node(  # type: ignore
        description="Takes in the url of a website",
        name="request_node",
        output_params=[
            OutputParameter(
                param_type="str",
                name="url",
                description="The url of the website",
            ),
            OutputParameter(
                param_type="str",
                name="format",
                description="the format to convert the webpage too",
            ),
        ],
    ),
    Node(  # type: ignore
        description="Verifies that the url is valid",
        name="verify_url",
        input_params=[
            InputParameter(
                param_type="str",
                name="url",
                description="The url of the website",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="str",
                name="valid_url",
                description="The url of the website if it is valid",
            )
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Downloads the webpage",
        name="download_page",
        input_params=[
            InputParameter(
                param_type="str",
                name="valid_url",
                description="The url of the website if it is valid",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="str",
                name="html",
                description="The html of the webpage",
            )
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Converts the webpage to the desired format",
        name="convert_page",
        input_params=[
            InputParameter(
                param_type="str",
                name="html",
                description="The html of the webpage",
            ),
            InputParameter(
                param_type="str",
                name="format",
                description="the format to convert the webpage too",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="str",
                name="converted_page",
                description="The converted webpage",
            )
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        name="response_node",
        description="Returns the converted webpage",
        input_params=[
            InputParameter(
                param_type="str",
                name="converted_page",
                description="The converted webpage",
            )
        ],
        package_requirements=[],
    ),
]
