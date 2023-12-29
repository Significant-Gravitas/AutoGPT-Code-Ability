import click
import requests
from requests.auth import HTTPBasicAuth
import os


@click.command()
@click.option(
    "--description", prompt=True, help="Description of the code request"
)
@click.option("--user_id", default=1234, type=int, help="User ID")
@click.option(
    "--runner",
    type=click.Choice(["Server", "CLI"], case_sensitive=False),
    prompt=True,
    help="Runner type",
)
@click.option("--username", default="admin", help="Username for authentication")
@click.option(
    "--password",
    default="asd453jnsdof9384rjnsdf",
    hide_input=True,
    help="Password for authentication",
)
@click.option(
    "--output",
    default="downloaded_file.zip",
    help="Output file path (default: downloaded_file.zip)",
)
def send_request(
    description: str,
    user_id: int,
    runner: str,
    username: str,
    password: str,
    output: str,
) -> None:
    url = "http://127.0.0.1:8000/code" 
    data = {"description": description, "user_id": user_id, "runner": runner}

    try:
        response = requests.post(
            url, json=data, auth=HTTPBasicAuth(username, password)
        )

        if response.status_code == 200:
            with open(output, "wb") as f:
                f.write(response.content)
            click.echo(f"File downloaded successfully: {output}")
        else:
            click.echo(
                f"Failed to download file. Status Code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    send_request()
