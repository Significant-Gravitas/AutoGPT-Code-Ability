from typing import Callable

from fastapi import Request
from prisma.enums import DevelopmentPhase
from starlette.middleware.base import BaseHTTPMiddleware

from codex.api_model import Identifiers
from codex.common.logging import execute_and_log


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log All Non-GET Requests & Responses and Exceptions into a 500 Error with the Exception Message
    Logging will be using logging.execute_and_log
    """

    LOGGED_API_PATH: dict[str, tuple[DevelopmentPhase, str]] = {
        "deployments": (DevelopmentPhase.DEPLOYMENT, "deployment_id"),
        "deliverables": (DevelopmentPhase.DEVELOPMENT, "completed_app_id"),
        "interview": (DevelopmentPhase.REQUIREMENTS, "interview_id"),
    }

    def get_matching_dev_phase(self, path_names: list[str]) -> str | None:
        for name in reversed(path_names):
            if name in self.LOGGED_API_PATH:
                return name
        return None

    def extract_id(self, url: str, path: str) -> str | None:
        # This function extracts the identifier from the URL path.
        # Middleware is executed before the routing, so path_params are not available.
        # pattern "{path}/{id}" -> "id"
        split = url.split(f"{path}/")
        if len(split) < 2:
            return None
        return split[1].split("/")[0]

    async def dispatch(self, request: Request, call_next: Callable):
        if request.method == "GET":
            return await call_next(request)

        path = request.url.path
        path_names = path.strip("/").split("/")
        dev_phase = self.get_matching_dev_phase(path_names)

        if dev_phase is None:
            return await call_next(request)

        # get all identifier from the path parameters
        identifiers = Identifiers(
            user_id=self.extract_id(path, "user"),
            app_id=self.extract_id(path, "apps"),
            interview_id=self.extract_id(path, "interview"),
            spec_id=self.extract_id(path, "specs"),
            completed_app_id=self.extract_id(path, "deliverables"),
            deployment_id=self.extract_id(path, "deployments"),
            compiled_route_id=self.extract_id(path, "routes"),  # unsed
            function_id=self.extract_id(path, "functions"),  # unused
        )

        # get event name using the request method and path template.
        # event_name = METHOD-PATH, e.g. POST-/user/{user_id}/apps/{app_id}/specs/
        path_template = path
        ids_dict = identifiers.model_dump()
        for key, value in ids_dict.items():
            if value:
                path_template = path_template.replace(value, "{" + key + "}")
        event_name = f"{request.method}-{path_template}"

        # get dev_phase and identifier key
        dev_phase, key = self.LOGGED_API_PATH[dev_phase]

        return await execute_and_log(
            id=identifiers,
            step=dev_phase,
            event=event_name,
            key=ids_dict[key],
            func=call_next,
            request=request,  # call_next's argument
        )
