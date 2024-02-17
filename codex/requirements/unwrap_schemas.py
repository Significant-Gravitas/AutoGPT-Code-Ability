from codex.requirements.model import (
    DatabaseSchema,
    DatabaseTable,
    DBSchemaResponseWrapper,
    Endpoint,
    EndpointDataModel,
    EndpointSchemaRefinementResponse,
    NewAPIModelWrapper,
    Parameter,
    ParameterWrapper,
    RequestModel,
    ResponseModel,
)


def unwrap_db_schema(input: DBSchemaResponseWrapper) -> DatabaseSchema:
    name = input.name
    description = input.description
    tables = input.tables
    unwrapped_tables: list[DatabaseTable] = [table for table in tables]
    return DatabaseSchema(name=name, description=description, tables=unwrapped_tables)


def unwrap_params(
    input: list[ParameterWrapper] | ParameterWrapper | str | None,
) -> list[Parameter]:
    wrapped_array: list[ParameterWrapper] | list[ParameterWrapper | str | None] = (
        input if isinstance(input, list) else [input]
    )
    params: list[Parameter] = []
    for param in wrapped_array:
        if isinstance(param, str):
            continue
        if param and param.param:
            params.append(param.param)
    return params


def unwrap_new_models(
    input: str | NewAPIModelWrapper | list[NewAPIModelWrapper] | None,
) -> list[EndpointDataModel]:
    if isinstance(input, type(None)):
        return []
    elif isinstance(input, str):
        if len(input) >= 0:
            return [
                EndpointDataModel(
                    name="Unnamed Data Model",
                    description="No Description Provided",
                    params=[
                        Parameter(
                            name="Unnamed Parameter",
                            param_type="str",
                            description=input,
                        )
                    ],
                )
            ]
        else:
            return []
    else:
        models: list[EndpointDataModel] = []
        wrapped_models: list[NewAPIModelWrapper] = (
            input if isinstance(input, list) else [input]
        )
        for wrapped in wrapped_models:
            model = wrapped.model
            endpoint_data_model = EndpointDataModel(
                name=model.name,
                description=model.description,
                params=unwrap_params(model.params),
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
        request_params = unwrap_params(input.api_endpoint.request_model.params)
        response_params = unwrap_params(input.api_endpoint.response_model.params)
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
