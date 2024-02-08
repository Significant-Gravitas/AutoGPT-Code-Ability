from prisma import Prisma
from prisma.models import Application, CodexUser, Specification

from codex.api_model import Indentifiers

from .model import ApplicationRequirements


async def create_spec(ids: Indentifiers, spec: ApplicationRequirements, db: Prisma):
    user = await CodexUser.prisma().find_unique_or_raise(
        where={
            "id": 1,
        }
    )

    app = await Application.prisma().find_first_or_raise(
        where={
            "id": ids.app_id,
            "userId": ids.user_id,
        }
    )

    routes = []

    for route in spec.api_routes:
        create_request = {
            "name": route.request_model.name,
            "description": route.request_model.description,
            "params": {
                "create": [
                    {
                        "name": param.name,
                        "description": param.description,
                        "param_type": param.param_type,
                    }
                    for param in route.request_model.params
                ],
            },
        }
        create_response = {
            "name": route.response_model.name,
            "description": route.response_model.description,
            "params": {
                "create": [
                    {
                        "name": param.name,
                        "description": param.description,
                        "param_type": param.param_type,
                    }
                    for param in route.response_model.params
                ],
            },
        }

        create_db = None
        if route.database_schema:
            create_db = {
                "description": route.database_schema.description,
                "tables": {
                    "create": [
                        {
                            "description": table.description,
                            "definition": table.definition,
                        }
                        for table in route.database_schema.tables
                    ],
                },
            }
        create_route = {
            "method": route.method,
            "path": route.path,
            "description": route.description,
            "requestObjects": {"create": create_request},
            "responseObject": {"create": create_response},
        }
        if create_db:
            create_route["schemas"] = {"create": create_db}
        routes.append(create_route)

    create_spec = {
        "name": spec.name,
        "context": spec.context,
        "User": {"connect": {"id": ids.user_id}},
        "app": {"connect": {"id": ids.app_id}},
        "apiRoutes": {"create": routes},
    }
    import json

    with open("create.json", "w") as f:
        f.write(json.dumps(create_spec, indent=4))

    new_spec = await Specification.prisma().create(data=create_spec)
    return new_spec
