import enum

import pydantic


class ChatRequest(pydantic.BaseModel):
    message: str


class ChatResponse(pydantic.BaseModel):
    id: str
    message: str


class PhaseStates(enum.Enum):
    NotStarted = 0
    InProgress = 1
    ErrorOccurred = 2
    SuccessfullyCompleted = 3


class AppStatus(pydantic.BaseModel):
    id: str
    features: PhaseStates
    modules: PhaseStates
    module_routes: PhaseStates
    api_routes: PhaseStates
    write_functions: PhaseStates
    compile_app: PhaseStates
    deploy_app: PhaseStates

    def __str__(self) -> str:
        """
        Writes thes status of the app in human readable format.
        """
        status_string = "App Status: \n"
        status_string += (
            f"- Features: {self.features.name}\n"
            if self.features != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- Modules: {self.modules.name}\n"
            if self.modules != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- Module Routes: {self.module_routes.name}\n"
            if self.module_routes != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- API Routes: {self.api_routes.name}\n"
            if self.api_routes != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- Write Functions: {self.write_functions.name}\n"
            if self.write_functions != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- Compile App: {self.compile_app.name}\n"
            if self.compile_app != PhaseStates.NotStarted
            else ""
        )
        status_string += (
            f"- Deploy App: {self.deploy_app.name}\n"
            if self.deploy_app != PhaseStates.NotStarted
            else ""
        )
        return status_string

    def possible_actions(self):
        actions = []

        # TODO - Add logic to determine possible actions based on the current state of the app

        if self.features == PhaseStates.NotStarted:
            actions.append("Add Features")

        if (
            self.modules == PhaseStates.NotStarted
            and self.features == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Add Modules")

        if (
            self.module_routes == PhaseStates.NotStarted
            and self.modules == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Add Module Routes")

        if (
            self.api_routes == PhaseStates.NotStarted
            and self.module_routes == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Add API Routes")

        if (
            self.write_functions == PhaseStates.NotStarted
            and self.api_routes == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Write Functions")

        if (
            self.compile_app == PhaseStates.NotStarted
            and self.write_functions == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Compile App")

        if self.compile_app == PhaseStates.InProgress:
            actions.append("Check Compile App Status")

        if self.compile_app == PhaseStates.ErrorOccurred:
            actions.append("Check Deploy App Status")

        if (
            self.deploy_app == PhaseStates.NotStarted
            and self.compile_app == PhaseStates.SuccessfullyCompleted
        ):
            actions.append("Deploy App")
