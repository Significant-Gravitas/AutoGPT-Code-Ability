import logging
import uuid
from datetime import datetime

from codex.interview.model import Interview, InterviewMessageWithResponseOptionalId

logger = logging.getLogger(__name__)


def availability_checker_interview() -> Interview:
    interiew = Interview(
        app_name="Availability Checker",
        project_description="Function that returns the availability of professionals, updating based on current activity or schedule.",
        questions=[
            # InterviewMessageWithResponseOptionalId(
            #     tool="ask",
            #     content="Do we need to check the availability of professionals?",
            #     response="Yes",
            #     id=None,
            # ),
            # InterviewMessageWithResponseOptionalId(
            #     tool="ask",
            #     content="What is the context of the function?",
            #     response="Function that returns the availability of professionals, updating based on current activity or schedule.",
            #     id=None,
            # ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )

    return interiew


# Function to define requirements for the Invoice Generator
def invoice_generator_interview() -> Interview:
    interview = Interview(
        app_name="Invoice Generator",
        project_description="The Dynamic Invoice Generator is a backend function designed to create detailed invoices for professional services. This function will process input data regarding services rendered, billable hours, parts used, and applicable rates or taxes, to generate a comprehensive invoice. This function operates without the need for database access, relying solely on the input provided at the time of invoice creation.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What software do you currently use",
                response="None",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What kind of services are you providing?",
                response="Professional services like consulting, design, or development.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What kind of items are used for the services?",
                response="Items used could include software licenses, hardware components, or other consumables.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


# Function to define requirements for the Appointment Optimization Tool
def appointment_optimization_interview() -> Interview:
    interview = Interview(
        app_name="Appointment Optimization Tool",
        project_description="The function for suggesting optimal appointment slots is designed to provide professionals and clients with the best possible meeting times based on the professional's availability, preferred working hours, and travel time considerations. This function operates in real-time, relying on input data without needing access to a database.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="How do you manage your calendar right now?",
                response="I use a calendar app to manage my appointments.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are your preferred working hours?",
                response="I prefer to work from 9 AM to 5 PM.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


# Function to define requirements for the Distance Calculator
def distance_calculator_interview() -> Interview:
    interview = Interview(
        app_name="Distance Calculator",
        project_description="The Distance Calculator is a tool that calculates the distance between the professional's and the client's locations to aid in planning travel time for appointments.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="How should the distance be calculated?",
                response="The distance should be calculated in both kilometers and miles.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


def profile_management() -> Interview:
    interview = Interview(
        app_name="Profile Management System",
        project_description="This system manages client and professional profiles, including operations for creating, updating, retrieving, and deleting profiles.",
        questions=[
            # InterviewMessageWithResponseOptionalId(
            #     tool="ask",
            #     content="What are the requirements for the profile management system?",
            #     response="This system manages client and professional profiles, including operations for creating, updating, retrieving, and deleting profiles.",
            #     id=None,
            # ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


def calendar_booking_system() -> Interview:
    interview = Interview(
        app_name="Calendar Booking System",
        project_description="A system that allows clients to book appointments with professionals based on their availability.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the requirements for the calendar booking system?",
                response="The system should allow clients to view the availability of professionals and book appointments based on their availability.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the main challenges faced with the current booking process?",
                response="The main challenges include manual scheduling, difficulty in finding available time slots, and lack of real-time updates.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


def inventory_mgmt_system() -> Interview:
    interview = Interview(
        app_name="InvenTrack",
        project_description="A tool designed to handle the tracking of inventory levels and usage for each client service. This includes the capability to add, update, and delete inventory items. To facilitate these functionalities, a set of API endpoints will be implemented.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the requirements for the inventory management system?",
                response="The system should allow users to add, update, and delete inventory items. It should also track inventory levels and usage for each client service.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What tools or software are currently used for inventory management?",
                response="We currently use a combination of spreadsheets and manual tracking methods.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the main challenges faced with the current inventory management process?",
                response="The main challenges include manual data entry, lack of real-time tracking, and difficulty in managing inventory levels for different client services.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="search",
                content="What are the best practices for inventory management?",
                response="Best practices for inventory management include real-time tracking, automated data entry, and categorization of inventory items based on client services.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )

    return interview


def invoice_payment_tracking() -> Interview:
    interview = Interview(
        app_name="FinFlow",
        project_description="The backend for managing invoicing, tracking payments, and handling financial reports and insights. It should consist of robust API routes to handle functionalities related to financial transactions.",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="How do you currently manage invoicing and payments?",
                response="We currently use a combination of spreadsheets and manual tracking methods.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="How effective is the current process for tracking payments?",
                response="The current process is time-consuming and prone to errors, making it difficult to track payments effectively.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What key improvements are you hoping to achieve with the new system?",
                response="We are looking to automate the invoicing process, track payments in real-time, and generate comprehensive financial reports.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the main challenges faced with the current financial tracking process?",
                response="The main challenges include manual data entry, lack of real-time tracking, and difficulty in generating comprehensive financial reports.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview

def ticktacktoe_game() -> Interview:
    interview = Interview(
        app_name="TicTacToe",
        project_description="A simple game of TicTacToe",
        questions=[
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the requirements for the game?",
                response="The game should allow two players to take turns marking the spaces in a 3x3 grid. The player who succeeds in placing three of their marks in a horizontal, vertical, or diagonal row is the winner.",
                id=None,
            ),
            InterviewMessageWithResponseOptionalId(
                tool="ask",
                content="What are the main challenges faced with the current game?",
                response="The main challenges include manual data entry, lack of real-time tracking, and difficulty in generating comprehensive financial reports.",
                id=None,
            ),
        ],
        id=str(uuid.uuid4()),
        createdAt=datetime.now(),
    )
    return interview


if __name__ == "__main__":
    from codex.common.logging_config import setup_logging

    setup_logging()
    logger.info(availability_checker_interview())
    logger.info(invoice_generator_interview())
    logger.info(appointment_optimization_interview())
    logger.info(distance_calculator_interview())
    logger.info(profile_management())
    logger.info(calendar_booking_system())
    logger.info(inventory_mgmt_system())
    logger.info(invoice_payment_tracking())
