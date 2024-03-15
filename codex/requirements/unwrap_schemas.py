from codex.requirements.model import (
    DatabaseSchema,
    Endpoint,
    EndpointSchemaRefinementResponse,
)


def convert_endpoint(
    input: EndpointSchemaRefinementResponse | list[EndpointSchemaRefinementResponse],
    existing: Endpoint,
    database: DatabaseSchema | None = None,
) -> Endpoint:
    if isinstance(input, list):
        # This thing is somehow a list?
        raise ValueError("This shouldn't be a list")
    if isinstance(input, EndpointSchemaRefinementResponse):
        request_params = input.api_endpoint.request_model
        response_params = input.api_endpoint.response_model

        request_model = request_params
        response_model = response_params
        existing.database_schema = database
        existing.request_model = request_model
        existing.response_model = response_model
        # existing.data_models = data_models
        return existing
