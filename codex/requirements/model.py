import logging
from enum import Enum

from pydantic import BaseModel

from codex.api_model import DatabaseSchema
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
    URL_SHORTENER_API = "URL Shortener API"
    QR_CODE_GENERATOR_API = "QR Code Generator API"
    CURRENCY_EXCHANGE_RATE_API = "Currency Exchange Rate API"
    CURRENCY_EXCHANGER_API = "Currency Exchanger API"
    IP_GEOLOCATION_API = "IP Geolocation API"
    IMAGE_RESIZING_API = "Image Resizing API"
    PASSWORD_STRENGTH_CHECKER_API = "Password Strength Checker API"
    TEXT_TO_SPEECH_API = "Text-to-Speech API"
    BARCODE_GENERATOR_API = "Barcode Generator API"
    EMAIL_VALIDATION_API = "Email Validation API"
    TIME_ZONE_CONVERSION_API = "Time Zone Conversion API"
    URL_PREVIEW_API = "URL Preview API"
    PDF_WATERMARKING_API = "PDF Watermarking API"
    RSS_FEED_TO_JSON_API = "RSS Feed to JSON API"
    DEVELOPER_TOOLKIT = "Developer Toolkit"
    TUTOR_APP = "Tutor App"
    FITNESS_AND_HEALTH_APP = "Fitness and Health App"
    AI_CHAT_ASSISTANT = "AI Chat Assistant"

    @staticmethod
    def get_task_description(task):
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
            case ExampleTask.URL_SHORTENER_API:
                return "Endpoint accepts a long URL as input, generates a unique short alias, stores the mapping, and returns the shortened URL."
            case ExampleTask.QR_CODE_GENERATOR_API:
                return "Endpoint takes in data, generates a customizable QR code image encoding the input data, and returns the image."
            case ExampleTask.CURRENCY_EXCHANGE_RATE_API:
                return "Endpoint accepts base and target currency codes, retrieves real-time exchange rate data, and returns the exchange rate."
            case ExampleTask.CURRENCY_EXCHANGER_API:
                return "Endpoint accepts base currency, target currency, and value, retrieves exchange rate, converts the value, and returns the result."
            case ExampleTask.IP_GEOLOCATION_API:
                return "Endpoint takes in an IP address, queries a geolocation database, and returns location data such as country, city, etc."
            case ExampleTask.IMAGE_RESIZING_API:
                return "Accepts an image file and desired dimensions, resizes the image, optionally crops it, and returns the resized image."
            case ExampleTask.PASSWORD_STRENGTH_CHECKER_API:
                return "Endpoint accepts a password string, analyzes its strength, returns a score, and provides suggestions for improvement."
            case ExampleTask.TEXT_TO_SPEECH_API:
                return "Endpoint accepts text input, converts it to natural-sounding speech audio, allows customization, and returns the audio file."
            case ExampleTask.BARCODE_GENERATOR_API:
                return "Accepts product data, generates a customizable barcode image in a specified format, and returns the image file."
            case ExampleTask.EMAIL_VALIDATION_API:
                return "Endpoint takes in an email address, verifies its format and existence, performs additional checks, and returns validation result."
            case ExampleTask.TIME_ZONE_CONVERSION_API:
                return "Accepts a timestamp and source time zone, converts it to a target time zone, and returns the converted timestamp."
            case ExampleTask.URL_PREVIEW_API:
                return "Endpoint accepts a URL, retrieves webpage content, extracts metadata, generates a preview snippet, and returns structured data."
            case ExampleTask.PDF_WATERMARKING_API:
                return "Accepts a PDF file and watermark, overlays the watermark onto each page, allows customization, and returns the watermarked PDF."
            case ExampleTask.RSS_FEED_TO_JSON_API:
                return "Endpoint takes in an RSS feed URL, parses the XML, extracts feed metadata and item details, and returns JSON representation."
            case ExampleTask.DEVELOPER_TOOLKIT:
                return "A comprehensive suite of single-endpoint APIs for various tasks, including QR codes, currency exchange, geolocation, and more."
            case ExampleTask.TUTOR_APP:
                return "An app that connects students with tutors, allows scheduling sessions, real-time communication, and progress tracking"
            case ExampleTask.FITNESS_AND_HEALTH_APP:
                return "An app to track workouts, nutrition, sleep, and vital signs, with personalized recommendations and goal setting features."
            case ExampleTask.AI_CHAT_ASSISTANT:
                return "An AI-powered chat assistant integrated with emails, Discord/Slack, capable of taking notes and managing a Kanban board."
            case _:
                raise NotImplementedError(f"Example Task {task.value} not implemented")


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
