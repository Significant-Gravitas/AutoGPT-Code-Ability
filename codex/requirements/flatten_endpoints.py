from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from codex.requirements.model import (
    Endpoint,
    EndpointGroupWrapper,
    EndpointWrapper,
)


def flatten_endpoints(
    input: list[EndpointGroupWrapper] | EndpointGroupWrapper,
) -> list[Endpoint]:
    endpoints = []
    if isinstance(input, list):
        for i in input:
            group = i.endpoint_group
            if isinstance(group, str):
                print(f"No endpoints here: {group}")
                continue
            elif isinstance(group, EndpointWrapper):
                endpoints.append(group.endpoint)
            elif isinstance(group, list):
                for i in group:
                    endpoints.append(i.endpoint)
    else:
        group = input.endpoint_group
        if isinstance(group, str):
            print(f"No endpoints here: {group}")
        elif isinstance(group, EndpointWrapper):
            endpoints.append(group.endpoint)
        elif isinstance(group, list):
            for i in group:
                endpoints.append(i.endpoint)

    return endpoints
