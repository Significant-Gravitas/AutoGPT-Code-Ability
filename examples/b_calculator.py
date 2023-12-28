from codex.model import InputParameter, Node, OutputParameter

nodes = [
    Node(  # type: ignore
        description="Receives input for the calculation",
        name="input_node",
        output_params=[
            OutputParameter(
                param_type="float", name="number1", description="The first number"
            ),
            OutputParameter(
                param_type="float", name="number2", description="The second number"
            ),
            OutputParameter(
                param_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
    ),
    Node(  # type: ignore
        description="Validates the numbers and operation",
        name="validation_node",
        input_params=[
            InputParameter(
                param_type="float", name="number1", description="The first number"
            ),
            InputParameter(
                param_type="float", name="number2", description="The second number"
            ),
            InputParameter(
                param_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="bool",
                name="is_valid",
                description="Whether the input is valid",
            ),
        ],
    ),
    Node(  # type: ignore
        description="Performs the calculation based on the operation",
        name="calculation_node",
        input_params=[
            InputParameter(
                param_type="float", name="number1", description="The first number"
            ),
            InputParameter(
                param_type="float", name="number2", description="The second number"
            ),
            InputParameter(
                param_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
        output_params=[
            OutputParameter(
                param_type="float",
                name="result",
                description="The result of the calculation",
            ),
        ],
    ),
    Node(  # type: ignore
        name="response_node",
        description="Formats and returns the result of the calculation",
        input_params=[
            InputParameter(
                param_type="float",
                name="result",
                description="The result of the calculation",
            ),
        ],
    ),
]
