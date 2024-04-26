from prisma.enums import AccessLevel, HTTPVerb
from pydantic import BaseModel

from codex.api_model import Identifiers, Specification
from codex.common.ai_block import AIBlock, ValidatedResponse, ValidationError
from codex.database import get_app_by_id
from codex.requirements.agent import APIRouteSpec, Module, SpecHolder
from codex.requirements.database import create_specification


class PageDecompositionEntry(BaseModel):
    route: str
    main_function_name: str
    description: str
    components: list[str]
    used_functions: list[str]


class PageDecompositionResponse(BaseModel):
    pages: list[PageDecompositionEntry]


class PageDecompositionBlock(AIBlock):
    """
    This is a block that handles, decomposing of front-end pages
    from the completed back-end app (CompletedApp)
    """

    prompt_template_name = "requirements/page_decompose"
    model = "gpt-4-turbo"
    is_json_response = True
    pydantic_object = PageDecompositionResponse

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        try:
            model = PageDecompositionResponse.model_validate_json(
                response.response, strict=False
            )
            response.response = model
            available_functions = invoke_params["available_functions"]

            for page in model.pages:
                for func_name in page.used_functions:
                    if func_name not in available_functions:
                        raise ValidationError(
                            f"Function {func_name} not found in available functions for page {page.route}"
                        )
                funcname = page.main_function_name
                if not funcname.startswith("render_") or not funcname.endswith("_page"):
                    raise ValidationError(
                        f"Main function name {page.main_function_name} should start with 'render_' and end with '_page'"
                    )

        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

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
                            + " with it's content: "
                            + ", ".join(page.components)
                            + ". It will utilize these functions: "
                            + ", ".join(page.used_functions),
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
        return await create_specification(spec_holder)
