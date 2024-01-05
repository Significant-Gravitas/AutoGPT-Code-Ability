import click
import requests
from requests.auth import HTTPBasicAuth


def send_request_cmd(
    description: str,
    user_id: int,
    username: str,
    password: str,
    output: str,
) -> None:
    url = "http://127.0.0.1:8000/code"
    data = {"description": description, "user_id": user_id}

    try:
        response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            with open(output, "wb") as f:
                f.write(response.content)
            click.echo(f"File downloaded successfully: {output}")
        else:
            click.echo(f"Failed to download file. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--description", prompt=True, help="Description of the code request")
@click.option("--user_id", default=1234, type=int, help="User ID")
@click.option("--username", default="admin", help="Username for authentication")
@click.option(
    "--password",
    default="asd453jnsdof9384rjnsdf",
    hide_input=True,
    help="Password for authentication",
)
@click.option(
    "--output",
    default="code_output.zip",
    help="Output file path (default: downloaded_file.zip)",
)
def send_request(
    description: str,
    user_id: int,
    username: str,
    password: str,
    output: str,
) -> None:
    send_request_cmd(description, user_id, username, password, output)


@cli.command(help="Run tests for all predefined descriptions.")
def run_tests():
    test_descriptions = [
        (
            "webpage_to_markdown.zip",
            "Develop a small script that takes a URL as input and returns the webpage in Markdown format. Focus on converting basic HTML tags like headings, paragraphs, and lists.",
        ),
        (
            "basic_calculator_api.zip",
            "Create a REST API that performs basic arithmetic operations (add, subtract, multiply, divide). The API should accept two numbers and an operation as input and return the result.",
        ),
        (
            "data_aggregation_tool.zip",
            "Build a tool that reads data from multiple sources (e.g., CSV, JSON files) and aggregates it into a single structured format. Include error handling for inconsistent or invalid data.",
        ),
        (
            "simple_blog_platform.zip",
            "Develop a basic blog platform where users can create, edit, and delete posts. Implement user authentication and a simple text editor for post creation.",
        ),
        (
            "inventory_management_system.zip",
            "Create a system to manage inventory for a small business. Features should include adding, updating, and deleting inventory items, as well as tracking stock levels.",
        ),
        (
            "real_time_chat_app.zip",
            "Develop a real-time chat application where users can send and receive messages instantly. Include features like user presence, typing indicators, and read receipts.",
        ),
        (
            "task_scheduler_reminder_system.zip",
            "Build a system where users can schedule tasks and set reminders. Include functionalities for recurring tasks, notifications, and calendar integration.",
        ),
        (
            "personal_finance_tracker.zip",
            "Create a personal finance tracking application that categorizes expenses and incomes. Offer insights based on spending patterns and suggest budgeting tips.",
        ),
        (
            "iot_device_data_analytics.zip",
            "Develop a platform that collects data from various IoT devices, stores it, and performs analytics to provide actionable insights. Include real-time data processing and visualization.",
        ),
        (
            "ecommerce_store_social_features.zip",
            "Build a comprehensive e-commerce platform with social features. This includes product listing, shopping cart, checkout process, user reviews, and social interactions like sharing products, following users, and creating wish lists.",
        ),
    ]

    for zip_file, description in test_descriptions:
        click.echo(f"Testing: {description}")
        send_request_cmd(
            description=description,
            user_id=1234,
            username="admin",
            password="asd453jnsdof9384rjnsdf",
            output=zip_file,
        )


if __name__ == "__main__":
    cli()


if __name__ == "__main__":
    send_request()
