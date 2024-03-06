import asyncio
import logging
import os

import click
from dotenv import load_dotenv

from codex.common.logging_config import setup_logging
from codex.interview.agent import populate_database_interviews

logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--database",
    "-d",
    default="postgres://agpt_live:bnfaHGGSDF134345@127.0.0.1/codegen",
)
def populate_db(database):
    """Populate the database with test data"""
    import os

    from prisma import Prisma

    from codex.database import create_test_data
    from codex.requirements.agent import populate_database_specs

    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"] or database
    db = Prisma(auto_register=True)

    async def popdb():
        await db.connect()
        await create_test_data()
        await populate_database_interviews()
        await populate_database_specs()
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
def benchmark():
    """Run the benchmark tests"""
    from codex.benchmark import run_benchmark

    asyncio.run(run_benchmark())


@cli.command()
def example():
    from codex.benchmark import run_specific_benchmark
    from codex.requirements.model import ExampleTask

    i = 1
    click.echo("Select a test case:")

    for task in list(ExampleTask):
        click.echo(f"[{i}] {task.value}")
        i += 1
    print("------")
    case = int(input("Enter number of the case to run: "))

    task = list(ExampleTask)[case - 1]
    asyncio.run(run_specific_benchmark(task))


@cli.command()
def serve() -> None:
    import uvicorn

    from codex.common.ai_model import OpenAIChatClient

    OpenAIChatClient.configure({})
    os.environ.get("ENV", "CLOUD").lower() == "local"

    uvicorn.run(
        "codex.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )


if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    cli()
