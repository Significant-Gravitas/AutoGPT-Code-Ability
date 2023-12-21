from codex.model import Node, Parameter

nodes = [
    Node(
        description="Receives input for the calculation",
        name="input_node",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="float", name="number1", description="The first number"
            ),
            Parameter(
                prama_type="float", name="number2", description="The second number"
            ),
            Parameter(
                prama_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
        package_requirements=[],
    ),
    Node(
        description="Validates the numbers and operation",
        name="validation_node",
        input_params=[
            Parameter(
                prama_type="float", name="number1", description="The first number"
            ),
            Parameter(
                prama_type="float", name="number2", description="The second number"
            ),
            Parameter(
                prama_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
        output_params=[
            Parameter(
                prama_type="bool",
                name="is_valid",
                description="Whether the input is valid",
            ),
        ],
        package_requirements=[],
    ),
    Node(
        description="Performs the calculation based on the operation",
        name="calculation_node",
        input_params=[
            Parameter(
                prama_type="float", name="number1", description="The first number"
            ),
            Parameter(
                prama_type="float", name="number2", description="The second number"
            ),
            Parameter(
                prama_type="str",
                name="operation",
                description="The arithmetic operation",
            ),
        ],
        output_params=[
            Parameter(
                prama_type="float",
                name="result",
                description="The result of the calculation",
            ),
        ],
        package_requirements=[],
    ),
    Node(
        name="response_node",
        description="Formats and returns the result of the calculation",
        input_params=[
            Parameter(
                prama_type="float",
                name="result",
                description="The result of the calculation",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]
