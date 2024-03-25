import asyncio
import logging
import os

import click
from dotenv import load_dotenv

from codex.common.logging_config import setup_logging

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

    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"] or database
    db = Prisma(auto_register=True)

    async def popdb():
        await db.connect()
        await create_test_data()
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
@click.option(
    "--port",
    "-p",
    default=8000,
    help="Port number of the Codex server",
    type=int,
)
def benchmark(port: int = 8000):
    """Run the benchmark tests"""
    import prisma

    import codex.common.test_const
    import codex.runner
    from codex.requirements.model import ExampleTask

    base_url = f"http://127.0.0.1:{port}/api/v1"
    prisma_client = prisma.Prisma(auto_register=True)
    tasks = list(ExampleTask)

    async def run_tasks():
        awaitables = [
            codex.runner.run_task(
                task_name=task.value,
                task_description=ExampleTask.get_task_description(task),
                user_id=codex.common.test_const.user_id_1,
                prisma_client=prisma_client,
                base_url=base_url,
            )
            for task in tasks
        ]
        # Run all tasks concurrently
        await asyncio.gather(*awaitables)

    asyncio.get_event_loop().run_until_complete(run_tasks())
    asyncio.get_event_loop().run_until_complete(prisma_client.disconnect())


@cli.command()
@click.option(
    "-p",
    "--port",
    default=8000,
    help="Port number of the Codex server",
    type=int,
)
def example(port: int):
    import prisma

    import codex.common.test_const
    import codex.runner
    from codex.requirements.model import ExampleTask

    base_url = f"http://127.0.0.1:{port}/api/v1"
    prisma_client = prisma.Prisma(auto_register=True)
    i = 1
    click.echo("Select a test case:")
    examples = list(ExampleTask)
    for task in examples:
        click.echo(f"[{i}] {task.value}")
        i += 1

    print("------")
    case = int(input("Enter number of the case to run: "))

    task = examples[case - 1]
    asyncio.get_event_loop().run_until_complete(
        codex.runner.run_task(
            task_name=task.value,
            task_description=ExampleTask.get_task_description(task),
            user_id=codex.common.test_const.user_id_1,
            prisma_client=prisma_client,
            base_url=base_url,
        )
    )
    asyncio.get_event_loop().run_until_complete(prisma_client.disconnect())


@cli.command()
def analytics():
    """
    Run analytics to get template performance.
    """
    import codex.analytics

    asyncio.get_event_loop().run_until_complete(
        codex.analytics.get_template_performance()
    )


@cli.command()
def costs():
    import codex.analytics

    asyncio.get_event_loop().run_until_complete(codex.analytics.get_costs())


async def get_resume_points(prisma_client):
    import datetime

    import prisma.types
    from prisma.models import ResumePoint

    if not prisma_client.is_connected():
        await prisma_client.connect()

    resume_points = await ResumePoint.prisma().find_many(
        include=prisma.types.ResumePointInclude(
            Application=True,
            Interview=True,
            Specification=True,
            CompletedApp=True,
            Deployment=True,
        ),
        take=20,
        order=[{"updatedAt": "desc"}],
    )

    print(
        "\033[92m Todays\033[0m and\033[93m yesterdays\033[0m days resume points are colored:\n"
    )
    print(
        f"{'':<3} | {'updatedAt':<20} | {'name':<30} | {'Interview':<10} | {'Specification':<15} | {'CompletedApp':<12} | {'Deployment':<10}"
    )
    separation_row = f"{'-' * 3}-+-{'-' * 20}-+-{'-' * 30}-+-{'-' * 10}-+-{'-' * 15}-+-{'-' * 12}-+-{'-' * 10}"
    print(separation_row)
    # Print table rows
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    for i, resume_point in enumerate(resume_points):
        updated_at_date = datetime.datetime.fromisoformat(
            resume_point.updatedAt.isoformat().split(".")[0]
        ).date()

        # Determine the color based on the updated date
        if updated_at_date == today:
            color_code = "\033[92m"  # Green
        elif updated_at_date == yesterday:
            color_code = "\033[93m"  # Yellow
        else:
            color_code = "\033[0m"  # Reset to default
        row = [
            str(i + 1),
            resume_point.updatedAt.isoformat().split(".")[0],
            resume_point.name[:30],
            "✓" if resume_point.Interview and resume_point.Interview.finished else "X",
            "✓" if resume_point.specificationId else "X",
            "✓" if resume_point.completedAppId else "X",
            "✓" if resume_point.deploymentId else "X",
        ]
        formatted_row = f"{color_code}{row[0]:<3} | {row[1]:<20} | {row[2]:<30} | {row[3]:<10} | {row[4]:<15} | {row[5]:<12} | {row[6]:<10}\033[0m"
        print(formatted_row)
    return resume_points


@cli.command()
@click.option(
    "--port",
    "-p",
    default=8000,
    help="Port number of the Codex server",
    type=int,
)
def resume(port: int):
    import prisma

    import codex.runner

    base_url = f"http://127.0.0.1:{port}/api/v1"
    prisma_client = prisma.Prisma(auto_register=True)
    print("")
    resume_points = asyncio.get_event_loop().run_until_complete(
        get_resume_points(prisma_client)
    )
    print("\n")
    case = int(input("Select index of the app you want to resume: "))

    selected_resume_point = resume_points[case - 1]

    resume_prompt = "You can resume from, "
    resume_options = []
    valid_options = set()
    step = codex.runner.ResumeStep.INTERVIEW  # do this step

    resume_options.append("Beginning (b)")
    valid_options.add("b")
    valid_options.add("B")

    if selected_resume_point.interviewId:
        # Running from a completed Interview
        resume_options.append("Interview (i)")
        valid_options.add("i")
        valid_options.add("I")
    if selected_resume_point.specificationId:
        # Running from a completed Specification
        resume_options.append("Specification (s)")
        valid_options.add("s")
        valid_options.add("S")
    if selected_resume_point.completedAppId:
        # Running from a completed App
        resume_options.append("Completed App (c)")
        valid_options.add("c")
        valid_options.add("C")
    if selected_resume_point.deploymentId:
        resume_options.append("Deployment (d)")
        valid_options.add("d")
        valid_options.add("D")

    resume_prompt += ", ".join(resume_options) + "."
    resume_prompt += " Enter the letter of the option you want to resume from: "

    selection = input(resume_prompt)
    if selection not in valid_options:
        print(
            f"Invalid selection: {selection}. Please select from the options provided."
        )
        return

    if selection in set(["i", "I"]):
        step = codex.runner.ResumeStep.SPECIFICATION
        print("Resuming from interview...")

    if selection in set(["s", "S"]):
        print("Resuming from specification...")
        step = codex.runner.ResumeStep.DEVELOPMENT

    if selection in set(["c", "C"]):
        print("Resuming from the developed (completed) app...")
        step = codex.runner.ResumeStep.COMPILE

    if selection in set(["d", "D"]):
        print("Resuming from compiled app - Downloading file again...")
        step = codex.runner.ResumeStep.DOWNLOAD

    asyncio.get_event_loop().run_until_complete(
        codex.runner.resume(
            step=step,
            resume_point=selected_resume_point,
            prisma_client=prisma_client,
            base_url=base_url,
        )
    )
    asyncio.get_event_loop().run_until_complete(prisma_client.disconnect())


@cli.command()
def serve() -> None:
    import uvicorn

    from codex.common.ai_model import OpenAIChatClient

    OpenAIChatClient.configure({})

    uvicorn.run(
        app="codex.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )


if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    cli()
