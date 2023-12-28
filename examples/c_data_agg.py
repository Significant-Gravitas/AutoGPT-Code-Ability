from codex.model import InputParameter, Node, OutputParameter

nodes = [
    Node(  # type: ignore
        description="Initiates data aggregation process, "
        "collects information about data sources and output format",
        name="request_node",
        input_params=[],
        output_params=[
            OutputParameter(
                param_type="List[str]",
                name="source_paths",
                description="Paths to the data sources",
            ),
            OutputParameter(
                param_type="str",
                name="output_format",
                description="Desired format for the aggregated data",
            ),
        ],
        package_requirements=[],
    ),
    Node(  # type: ignore
        description="Reads data from each source and loads it into a data structure",
        name="read_data_node",
        input_params=[
            InputParameter(
                param_type="List[str]",
                name="source_paths",
                description="Paths to the data sources",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="List[DataFrame]",
                name="data_frames",
                description="List of DataFrames with the data from each source",
            ),
        ],
        package_requirements=["pandas"],
    ),
    Node(  # type: ignore
        description="Validates data for inconsistencies or invalid data in each source",
        name="validate_data_node",
        input_params=[
            InputParameter(
                param_type="List[DataFrame]",
                name="data_frames",
                description="List of DataFrames with the data from each source",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="List[DataFrame]",
                name="validated_data",
                description="Validated and potentially corrected DataFrames",
            ),
        ],
        package_requirements=["pandas"],
    ),
    Node(  # type: ignore
        description="Aggregates data from all sources into a single structured format",
        name="aggregate_data_node",
        input_params=[
            InputParameter(
                param_type="List[DataFrame]",
                name="validated_data",
                description="Validated DataFrames",
            )
        ],
        output_params=[
            OutputParameter(
                param_type="DataFrame",
                name="aggregated_data",
                description="Aggregated data in a single DataFrame",
            ),
        ],
        package_requirements=["pandas"],
    ),
    Node(  # type: ignore
        name="response_node",
        description="Outputs the aggregated data in the specified format",
        input_params=[
            InputParameter(
                param_type="DataFrame",
                name="aggregated_data",
                description="Aggregated data in a single DataFrame",
            ),
            InputParameter(
                param_type="str",
                name="output_format",
                description="Desired format for the aggregated data",
            ),
        ],
        output_params=[],
        package_requirements=[],
    ),
]
