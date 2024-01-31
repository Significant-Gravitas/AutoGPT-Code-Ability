import concurrent.futures

import click
import requests
from requests.auth import HTTPBasicAuth

test_descriptions = [
    (
        "01_webpage_to_markdown.zip",
        "Develop a small script that takes a URL as input and returns the webpage in Markdown format.",
    ),
    (
        "02_basic_calculator_api.zip",
        "Create a REST API that performs basic arithmetic operations (add, subtract, multiply, divide). The API should accept two numbers and an operation as input and return the result.",
    ),
    (
        "03_data_aggregation_tool.zip",
        "Build a tool that reads data from multiple sources (e.g., CSV, JSON files) and aggregates it into a single structured format. Include error handling for inconsistent or invalid data.",
    ),
    (
        "04_simple_blog_platform.zip",
        "Develop a basic blog platform where users can create, edit, and delete posts. Implement user authentication and a simple text editor for post creation.",
    ),
    (
        "05_inventory_management_system.zip",
        "Create a system to manage inventory for a small business. Features should include adding, updating, and deleting inventory items, as well as tracking stock levels.",
    ),
    (
        "06_real_time_chat_app.zip",
        "Develop a real-time chat application where users can send and receive messages instantly. Include features like user presence, typing indicators, and read receipts.",
    ),
    (
        "07_task_scheduler_reminder_system.zip",
        "Build a system where users can schedule tasks and set reminders. Include functionalities for recurring tasks, notifications, and calendar integration.",
    ),
    (
        "08_personal_finance_tracker.zip",
        "Create a personal finance tracking application that categorizes expenses and incomes. Offer insights based on spending patterns and suggest budgeting tips.",
    ),
    (
        "09_iot_device_data_analytics.zip",
        "Develop a platform that collects data from various IoT devices, stores it, and performs analytics to provide actionable insights. Include real-time data processing and visualization.",
    ),
    (
        "10_ecommerce_store_social_features.zip",
        "Build a comprehensive e-commerce platform with social features. This includes product listing, shopping cart, checkout process, user reviews, and social interactions like sharing products, following users, and creating wish lists.",
    ),
]


def worker(zip_file, description):
    click.echo(f"Testing: {description}")
    send_request_cmd(
        description=description,
        user_id=1234,
        username="admin",
        password="asd453jnsdof9384rjnsdf",
        output=zip_file,
    )


def send_request_cmd(
    description: str,
    user_id: int,
    username: str,
    password: str,
    output: str,
) -> None:
    import json

    url = "http://127.0.0.1:8000/code"
    data = {"description": description, "user_id": user_id}

    try:
        response = requests.post(url, json=data, auth=HTTPBasicAuth(username, password))

        if response.status_code == 200:
            with open(f"workspace/{output}", "wb") as f:
                f.write(response.content)
            click.echo(f"✅ File downloaded successfully: {output}")
        else:
            click.echo(
                f"❌ {output} - Failed to download file. Status Code: {response.status_code} - {json.loads(response.content)['detail']}"
            )
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


@cli.command()
def test() -> None:
    i = 1
    click.echo("Select a test case:")

    for file, description in test_descriptions:
        click.echo(f"[{i}] {description}")
        i += 1

    case = int(input("Case: "))

    file_name, description = test_descriptions[case - 1]

    click.echo(f"Testing: {description}")
    send_request_cmd(description, 333, "admin", "asd453jnsdof9384rjnsdf", file_name)


@cli.command(help="Run tests for all predefined descriptions.")
def run_tests():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(worker, zip_file, description)
            for zip_file, description in test_descriptions
        ]

        for future in concurrent.futures.as_completed(futures):
            future.result()  # You can handle exceptions here if needed


@cli.command()
def ng():
    from codex.chains.gen_branching_graph import NodeGraph

    graph = {
        "nodes": [
            {
                "name": "StartDivide",
                "node_type": "start",
                "description": "Start node for the division operation",
                "input_params": [],
                "output_params": [
                    {
                        "param_type": "float",
                        "name": "numerator",
                        "description": "The numerator for division",
                    },
                    {
                        "param_type": "float",
                        "name": "denominator",
                        "description": "The denominator for division",
                    },
                ],
                "next_node_name": "CheckForZero",
                "python_if_condition": None,
                "true_next_node_name": None,
                "elifs": None,
                "false_next_node_name": None,
            },
            {
                "name": "CheckForZero",
                "node_type": "if",
                "description": "Checks if the denominator is zero",
                "input_params": [
                    {
                        "param_type": "float",
                        "name": "denominator",
                        "description": "The denominator for division",
                    }
                ],
                "output_params": [],
                "next_node_name": None,
                "python_if_condition": "denominator == 0",
                "true_next_node_name": "RaiseDivideByZeroException",
                "elifs": None,
                "false_next_node_name": "PerformDivision",
            },
            {
                "name": "raise_exception",
                "node_type": "action",
                "description": "Raises an exception if the denominator is zero",
                "input_params": [
                    {
                        "param_type": "float",
                        "name": "denominator",
                        "description": "The denominator for division",
                    }
                ],
                "output_params": [
                    {
                        "param_type": "str",
                        "name": "error_message",
                        "description": "Error message for division by zero",
                    }
                ],
                "next_node_name": "EndDivide",
                "python_if_condition": None,
                "true_next_node_name": None,
                "elifs": None,
                "false_next_node_name": None,
            },
            {
                "name": "perform_division",
                "node_type": "action",
                "description": "Performs the division operation",
                "input_params": [
                    {
                        "param_type": "float",
                        "name": "numerator",
                        "description": "The numerator for division",
                    },
                    {
                        "param_type": "float",
                        "name": "denominator",
                        "description": "The denominator for division",
                    },
                ],
                "output_params": [
                    {
                        "param_type": "float",
                        "name": "result",
                        "description": "The result of division",
                    }
                ],
                "next_node_name": "EndDivide",
                "python_if_condition": None,
                "true_next_node_name": None,
                "elifs": None,
                "false_next_node_name": None,
            },
            {
                "name": "EndDivide",
                "node_type": "end",
                "description": "End node for the division operation",
                "input_params": [
                    {
                        "param_type": "float",
                        "name": "result",
                        "description": "The result of division",
                    }
                ],
                "output_params": [],
                "next_node_name": None,
                "python_if_condition": None,
                "true_next_node_name": None,
                "elifs": None,
                "false_next_node_name": None,
            },
        ]
    }
    NodeGraph.parse_obj(graph)


if __name__ == "__main__":
    cli()
