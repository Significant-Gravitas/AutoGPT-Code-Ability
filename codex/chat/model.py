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
        phase_actions = {
            PhaseStates.NotStarted: "Add",
            PhaseStates.InProgress: "Check",
            PhaseStates.ErrorOccurred: "Retry",
            PhaseStates.SuccessfullyCompleted: "Modify",
        }

        actions = []

        phases = [
            (self.features, "Features"),
            (self.modules, "Modules"),
            (self.module_routes, "Module Routes"),
            (self.api_routes, "API Routes"),
            (self.write_functions, "Functions"),
            (self.compile_app, "Compile App"),
            (self.deploy_app, "Deploy App"),
        ]

        for i, (phase, state) in enumerate(phases):
            if phase == PhaseStates.SuccessfullyCompleted:
                actions.append(f"{phase_actions[phase]} {state}")
                if i == len(phases) - 1:
                    break
            else:
                actions.append(f"{phase_actions[phase]} {state}")
                break

        return actions
