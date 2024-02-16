from codex.requirements.model import Endpoint, EndpointGroupWrapper


def flatten_endpoints(
    input: list[EndpointGroupWrapper],
) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    if isinstance(input, list):
        for group in input:
            for endpoint in group.endpoints:
                endpoints.append(endpoint)
    else:
        raise ValueError("Invalid input type")

    return endpoints
