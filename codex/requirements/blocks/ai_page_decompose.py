import re

from prisma.enums import AccessLevel, HTTPVerb
from pydantic import BaseModel

from codex.api_model import Identifiers, Specification
from codex.common.ai_block import (
    AIBlock,
    ListValidationError,
    ValidatedResponse,
)
from codex.database import get_app_by_id
from codex.requirements.agent import APIRouteSpec, Module, SpecHolder
from codex.requirements.database import (
    connect_db_schema_to_specification,
    create_specification,
    get_specification,
)


class PageDecompositionEntry(BaseModel):
    route: str
    main_function_name: str
    description: str
    components: list[str]
    used_functions: dict[str, str]


class PageConnection(BaseModel):
    to: str
    description: str


class PageDecompositionResponse(BaseModel):
    pages: list[PageDecompositionEntry]
    connections: dict[str, list[PageConnection]]


class PageDecompositionBlock(AIBlock):
    """
    This is a block that handles, decomposing of front-end pages
    from the completed back-end app (CompletedApp)
    """

    prompt_template_name = "requirements/page_decompose"
    model = "gpt-4o"
    is_json_response = True
    pydantic_object = PageDecompositionResponse

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        validation_errors = ListValidationError(
            "Error validating response for page decomposition"
        )

        try:
            model = PageDecompositionResponse.model_validate_json(
                response.response, strict=False
            )
            response.response = model
            available_functions = invoke_params["available_functions"]

            for page in model.pages:
                for func_name in page.used_functions:
                    if func_name not in available_functions:
                        validation_errors.append_message(
                            f"Function {func_name} not found in available functions for page {page.route}"
                        )
                funcname = page.main_function_name
                if not re.fullmatch(r"render_.*_page", funcname):
                    validation_errors.append_message(
                        f"Main function name {page.main_function_name} should start with 'render_' and end with '_page'"
                    )

            available_pages = {page.route for page in model.pages}

            if "/" not in available_pages:
                validation_errors.append_message(
                    "No page with route '/' as a home page is found"
                )

            for source_page, connections in model.connections.items():
                if source_page not in available_pages:
                    validation_errors.append_message(
                        f"Source page {source_page} you described in `connections` field not found in available pages"
                    )
                for connection in connections:
                    if connection.to not in available_pages:
                        validation_errors.append_message(
                            f"Destination page {connection.to} you described in `connections` field for source page {source_page} not found in available pages"
                        )

        except Exception as e:
            validation_errors.append_message(str(e))

        validation_errors.raise_if_errors()

        return response

    async def create_item(
        self,
        ids: Identifiers,
        validated_response: ValidatedResponse,
    ) -> Specification:
        if not ids.app_id:
            raise ValueError("app_id is required to create a new completed app")
        if not ids.user_id:
            raise ValueError("user_id is required to create a new completed app")
        if not ids.spec_id:
            raise ValueError("spec_id is required to create a new completed app")

        response: PageDecompositionResponse = validated_response.response
        app = await get_app_by_id(ids.user_id, ids.app_id)

        spec_holder = SpecHolder(
            ids=ids,
            app=app,
            modules=[
                Module(
                    name=app.name,
                    description=app.description or "",
                    api_routes=[
                        APIRouteSpec(
                            module_name=page.main_function_name,
                            http_verb=HTTPVerb.GET,
                            function_name=page.main_function_name,
                            path=page.route,
                            description="A page that renders "
                            + page.description
                            + "\n\nwith it's content:\n"
                            + "\n".join(page.components)
                            + "\n\nIt will utilize these functions:\n"
                            + "\n".join(
                                [
                                    f"  * '{name}': {desc}"
                                    for name, desc in page.used_functions.items()
                                ]
                            )
                            + "\n\nIt will connect to these pages:\n"
                            + "\n".join(
                                [
                                    f"  * `{conn.to}`: {conn.description}"
                                    for conn in response.connections.get(page.route, [])
                                ]
                            ),
                            access_level=AccessLevel.PUBLIC,
                            allowed_access_roles=[],
                            request_model=None,
                            response_model=None,
                        )
                        for page in response.pages
                    ],
                )
            ],
        )
        spec = await create_specification(spec_holder)
        parent_spec = await get_specification(ids.user_id, ids.app_id, ids.spec_id)
        if parent_spec.databaseSchemaId:
            spec.databaseSchemaId = await connect_db_schema_to_specification(
                spec.id, parent_spec.databaseSchemaId
            )
        return spec
