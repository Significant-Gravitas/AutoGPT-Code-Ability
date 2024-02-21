from codex.requirements.model import (
    DatabaseSchema,
    DBSchemaResponseWrapper,
    Endpoint,
    EndpointDataModel,
    EndpointSchemaRefinementResponse,
    NewAPIModel,
    RequestModel,
    ResponseModel,
)


def convert_db_schema(input: DBSchemaResponseWrapper) -> DatabaseSchema:
    return DatabaseSchema(
        name=input.name, description=input.description, tables=input.tables
    )


def unwrap_new_models(
    input: list[NewAPIModel] | None,
) -> list[EndpointDataModel]:
    if isinstance(input, type(None)):
        return []
    else:
        models: list[EndpointDataModel] = []

        for model in input:
            model = model
            endpoint_data_model = EndpointDataModel(
                name=model.name,
                description=model.description,
                params=model.params,
            )
            models.append(endpoint_data_model)
        return models


def convert_endpoint(
    input: EndpointSchemaRefinementResponse | list[EndpointSchemaRefinementResponse],
    existing: Endpoint,
    database: DatabaseSchema,
) -> Endpoint:
    if isinstance(input, list):
        # This thing is somehow a list?
        raise ValueError("This shouldn't be a list")
    if isinstance(input, EndpointSchemaRefinementResponse):
        request_params = input.api_endpoint.request_model.params
        response_params = input.api_endpoint.response_model.params
        data_models = unwrap_new_models(input.new_api_models)

        request_model = RequestModel(
            name=input.api_endpoint.request_model.name,
            description=input.api_endpoint.request_model.name,
            params=request_params,
        )
        response_model = ResponseModel(
            name=input.api_endpoint.request_model.name,
            description=input.api_endpoint.request_model.name,
            params=response_params,
        )
        existing.database_schema = database
        existing.request_model = request_model
        existing.response_model = response_model
        existing.data_models = data_models
        return existing
