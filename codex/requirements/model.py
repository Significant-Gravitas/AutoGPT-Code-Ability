import logging
from enum import Enum
from typing import List

from pydantic import BaseModel

import codex.common.test_const as test_consts
from codex.common.model import ObjectTypeModel as ObjectTypeE

logger = logging.getLogger(__name__)


class ExampleTask(Enum):
    AVAILABILITY_CHECKER = "Availability Checker"
    INVOICE_GENERATOR = "Invoice Generator"
    APPOINTMENT_OPTIMIZATION_TOOL = "Appointment Optimization Tool"
    DISTANCE_CALCULATOR = "Distance Calculator"
    PROFILE_MANAGEMENT_SYSTEM = "Profile Management System"
    CALENDAR_BOOKING_SYSTEM = "Calendar Booking System"
    INVENTORY_MANAGEMENT_SYSTEM = "Inventory Management System"
    INVOICING_AND_PAYMENT_TRACKING_SYSTEM = "Invoiceing and Payment Tracking System"
    TICTACTOE_GAME = "TicTacToe Game"

    @staticmethod
    def get_app_id(task):
        """
        Get the corresponding app ID based on the given task.
        If we do not have hardcoded requirements we return None

        Args:
            task (ExampleTask): The task for which to retrieve the app ID.

        Returns:
            str or None: The app ID corresponding to the task, or None if no app ID is available.

        Raises:
            NotImplementedError: If the given task is not implemented.

        """
        match task:
            case ExampleTask.AVAILABILITY_CHECKER:
                return test_consts.app_id_1
            case ExampleTask.INVOICE_GENERATOR:
                return test_consts.app_id_2
            case ExampleTask.APPOINTMENT_OPTIMIZATION_TOOL:
                return test_consts.app_id_3
            case ExampleTask.DISTANCE_CALCULATOR:
                return test_consts.app_id_4
            case ExampleTask.PROFILE_MANAGEMENT_SYSTEM:
                return test_consts.app_id_5
            case ExampleTask.CALENDAR_BOOKING_SYSTEM:
                # return test_consts.app_id_6
                return None
            case ExampleTask.INVENTORY_MANAGEMENT_SYSTEM:
                # return test_consts.app_id_7
                return None
            case ExampleTask.INVOICING_AND_PAYMENT_TRACKING_SYSTEM:
                # return test_consts.app_id_8
                return None
            case ExampleTask.TICTACTOE_GAME:
                return test_consts.app_id_11
            case _:
                raise NotImplementedError(f"Example Task {task.value} not implemented")

    @staticmethod
    def get_interview_id(task):
        """
        Get the interview ID based on the given task.
        If we do not have hardcoded requirements we return None

        Args:
            task (ExampleTask): The task for which to retrieve the interview ID.

        Returns:
            int or None: The interview ID corresponding to the task, or None if no interview ID is available.

        Raises:
            NotImplementedError: If the task is not implemented.

        """
        match task:
            case ExampleTask.AVAILABILITY_CHECKER:
                return test_consts.interview_id_1
            case ExampleTask.INVOICE_GENERATOR:
                return test_consts.interview_id_2
            case ExampleTask.APPOINTMENT_OPTIMIZATION_TOOL:
                return test_consts.interview_id_3
            case ExampleTask.DISTANCE_CALCULATOR:
                return test_consts.interview_id_4
            case ExampleTask.PROFILE_MANAGEMENT_SYSTEM:
                return test_consts.interview_id_5
            case ExampleTask.CALENDAR_BOOKING_SYSTEM:
                # return test_consts.interview_id_6
                return None
            case ExampleTask.INVENTORY_MANAGEMENT_SYSTEM:
                # return test_consts.interview_id_7
                return None
            case ExampleTask.INVOICING_AND_PAYMENT_TRACKING_SYSTEM:
                # return test_consts.interview_id_8
                return None
            case ExampleTask.TICTACTOE_GAME:
                return test_consts.interview_id_11
            case _:
                raise NotImplementedError(f"Example Task {task.value} not implemented")

    @staticmethod
    def get_task_description(task):
        """
        Returns the description of a given task.

        Parameters:
        - task: An instance of the ExampleTask enum.

        Returns:
        - A string representing the description of the task.

        Raises:
        - NotImplementedError: If the task is not implemented.
        """

        match task:
            case ExampleTask.AVAILABILITY_CHECKER:
                return "Function that returns the real-time availability of professionals, updating based on current activity or schedule."
            case ExampleTask.INVOICE_GENERATOR:
                return "Generates invoices based on services, billable hours, and parts used, with options for different rates and taxes."
            case ExampleTask.APPOINTMENT_OPTIMIZATION_TOOL:
                return "Suggests optimal appointment slots based on availability, working hours, and travel time considerations."
            case ExampleTask.DISTANCE_CALCULATOR:
                return "Calculates the distance between the professional's and client's locations for planning travel time."
            case ExampleTask.PROFILE_MANAGEMENT_SYSTEM:
                return "Allows creation and updating of client and professional profiles, storing contact info, preferences, and history."
            case ExampleTask.CALENDAR_BOOKING_SYSTEM:
                return "Enables booking, rescheduling, or canceling of appointments, and allows professionals to manage their schedules."
            case ExampleTask.INVENTORY_MANAGEMENT_SYSTEM:
                return "Tracks inventory levels and usage for each client service, including adding, updating, and deleting items."
            case ExampleTask.INVOICING_AND_PAYMENT_TRACKING_SYSTEM:
                return "Manages invoicing for services rendered, tracks payments, and handles financial reports and insights."
            case ExampleTask.TICTACTOE_GAME:
                return "Two Players TicTacToe Game communicate through an API."
            case _:
                raise NotImplementedError(f"Example Task {task.value} not implemented")


class DatabaseEnums(BaseModel):
    name: str
    description: str
    values: list[str]
    definition: str

    def __str__(self):
        return f"**Enum: {self.name}**\n\n**Values**:\n{', '.join(self.values)}\n"


class DatabaseTable(BaseModel):
    name: str | None = None
    description: str
    definition: str  # prisma model for a table

    def __str__(self):
        return f"**Table: {self.name}**\n\n\n\n**Definition**:\n```\n{self.definition}\n```\n"


class DatabaseSchema(BaseModel):
    name: str  # name of the database schema
    description: str  # context on what the database schema is
    tables: List[DatabaseTable]  # list of tables in the database schema
    enums: List[DatabaseEnums]

    def __str__(self):
        tables_str = "\n".join(str(table) for table in self.tables)
        enum_str = "\n".join(str(enum) for enum in self.enums)
        return f"## {self.name}\n**Description**: {self.description}\n**Tables**:\n{tables_str}\n**Enums**:\n{enum_str}\n"


class APIEndpointWrapper(BaseModel):
    request_model: ObjectTypeE
    response_model: ObjectTypeE


class EndpointSchemaRefinementResponse(BaseModel):
    think: str
    db_models_needed: list[str]
    api_endpoint: APIEndpointWrapper


class PreAnswer(BaseModel):
    tables: list[dict[str, str]]
    enums: list[dict[str, str]]


class DBResponse(BaseModel):
    think: str
    anti_think: str
    plan: str
    refine: str
    pre_answer: PreAnswer
    pre_answer_issues: str
    full_schema: str
    database_schema: DatabaseSchema
    conclusions: str
