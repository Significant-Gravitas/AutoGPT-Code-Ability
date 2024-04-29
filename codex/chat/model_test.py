from codex.chat.model import AppStatus, PhaseStates


class TestPossibleActions:
    # Returns a list of possible actions based on the current status of the app.
    def test_returns_list_of_possible_actions(self):
        # Initialize the class object
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.NotStarted,
            modules=PhaseStates.NotStarted,
            module_routes=PhaseStates.NotStarted,
            api_routes=PhaseStates.NotStarted,
            write_functions=PhaseStates.NotStarted,
            compile_app=PhaseStates.NotStarted,
            deploy_app=PhaseStates.NotStarted,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        
    def returns_next_step_if_phase_completed_1(self):
        # Initialize the class object
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.SuccessfullyCompleted,
            modules=PhaseStates.NotStarted,
            module_routes=PhaseStates.NotStarted,
            api_routes=PhaseStates.NotStarted,
            write_functions=PhaseStates.NotStarted,
            compile_app=PhaseStates.NotStarted,
            deploy_app=PhaseStates.NotStarted,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) == 2
        
        
    def returns_next_step_if_phase_completed_2(self):
        # Initialize the class object
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.SuccessfullyCompleted,
            modules=PhaseStates.SuccessfullyCompleted,
            module_routes=PhaseStates.NotStarted,
            api_routes=PhaseStates.NotStarted,
            write_functions=PhaseStates.NotStarted,
            compile_app=PhaseStates.NotStarted,
            deploy_app=PhaseStates.NotStarted,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) == 3


    # Returns a list of possible actions even if all phases have errors.
    def test_returns_list_of_possible_actions_with_errors(self):
        # Initialize the class object with all phases in error state
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.ErrorOccurred,
            modules=PhaseStates.ErrorOccurred,
            module_routes=PhaseStates.ErrorOccurred,
            api_routes=PhaseStates.ErrorOccurred,
            write_functions=PhaseStates.ErrorOccurred,
            compile_app=PhaseStates.ErrorOccurred,
            deploy_app=PhaseStates.ErrorOccurred,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) > 0

    # Returns only the first possible action if the first phase is in progress.
    def test_returns_first_possible_action_if_first_phase_in_progress(self):
        # Initialize the class object
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.InProgress,
            modules=PhaseStates.NotStarted,
            module_routes=PhaseStates.NotStarted,
            api_routes=PhaseStates.NotStarted,
            write_functions=PhaseStates.NotStarted,
            compile_app=PhaseStates.NotStarted,
            deploy_app=PhaseStates.NotStarted,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) == 1
        assert actions[0] == "Check Features"


    # Returns only the first possible action if the first phase is not started.
    def test_returns_first_possible_action_if_first_phase_not_started(self):
        # Initialize the class object
        app_status = AppStatus(
            id="app1",
            features=PhaseStates.NotStarted,
            modules=PhaseStates.NotStarted,
            module_routes=PhaseStates.NotStarted,
            api_routes=PhaseStates.NotStarted,
            write_functions=PhaseStates.NotStarted,
            compile_app=PhaseStates.NotStarted,
            deploy_app=PhaseStates.NotStarted,
        )

        # Invoke the method under test
        actions = app_status.possible_actions()

        # Assert the result
        assert isinstance(actions, list)
        assert len(actions) == 1
        assert actions[0] == "Add Features"
