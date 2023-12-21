from codex.model import Node, Parameter

request_node = Node(
    description="Initiates data aggregation process, "
    "collects information about data sources and output format",
    name="request_node",
    input_params=[],
    output_params=[
        Parameter(
            prama_type="List[str]",
            name="source_paths",
            description="Paths to the data sources",
        ),
        Parameter(
            prama_type="str",
            name="output_format",
            description="Desired format for the aggregated data",
        ),
    ],
    package_requirements=[],
)

read_data_node = Node(
    description="Reads data from each source and loads it into a data structure",
    name="read_data_node",
    input_params=[
        Parameter(
            prama_type="List[str]",
            name="source_paths",
            description="Paths to the data sources",
        )
    ],
    output_params=[
        Parameter(
            prama_type="List[DataFrame]",
            name="data_frames",
            description="List of DataFrames with the data from each source",
        ),
    ],
    package_requirements=["pandas"],
)

validate_data_node = Node(
    description="Validates data for inconsistencies or invalid data in each source",
    name="validate_data_node",
    input_params=[
        Parameter(
            prama_type="List[DataFrame]",
            name="data_frames",
            description="List of DataFrames with the data from each source",
        )
    ],
    output_params=[
        Parameter(
            prama_type="List[DataFrame]",
            name="validated_data",
            description="Validated and potentially corrected DataFrames",
        ),
    ],
    package_requirements=["pandas"],
)

aggregate_data_node = Node(
    description="Aggregates data from all sources into a single structured format",
    name="aggregate_data_node",
    input_params=[
        Parameter(
            prama_type="List[DataFrame]",
            name="validated_data",
            description="Validated DataFrames",
        )
    ],
    output_params=[
        Parameter(
            prama_type="DataFrame",
            name="aggregated_data",
            description="Aggregated data in a single DataFrame",
        ),
    ],
    package_requirements=["pandas"],
)

response_node = Node(
    name="response_node",
    description="Outputs the aggregated data in the specified format",
    input_params=[
        Parameter(
            prama_type="DataFrame",
            name="aggregated_data",
            description="Aggregated data in a single DataFrame",
        ),
        Parameter(
            prama_type="str",
            name="output_format",
            description="Desired format for the aggregated data",
        ),
    ],
    output_params=[],
    package_requirements=[],
)
