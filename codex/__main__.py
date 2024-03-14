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
        # await populate_database_interviews()
        # await populate_database_specs()
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
@click.option(
    "-h",
    "--hardcoded",
    is_flag=True,
    help="Flag indicating whether to use hardcoded values",
)
def benchmark(hardcoded: bool):
    """Run the benchmark tests"""
    from codex.benchmark import run_benchmark

    asyncio.run(run_benchmark(skip_requirements=hardcoded))


@cli.command()
@click.option(
    "-h",
    "--hardcoded",
    is_flag=True,
    help="Flag indicating whether to use hardcoded values",
)
def example(hardcoded: bool):
    from codex.benchmark import run_benchmark
    from codex.requirements.model import ExampleTask

    i = 1
    click.echo("Select a test case:")
    examples = list(ExampleTask)
    if hardcoded:
        examples: list[ExampleTask] = [
            task for task in examples if ExampleTask.get_app_id(task) is not None
        ]

    for task in examples:
        click.echo(f"[{i}] {task.value}")
        i += 1
    print("------")
    case = int(input("Enter number of the case to run: "))

    task = examples[case - 1]
    asyncio.run(run_benchmark(hardcoded, task))


async def get_resume_points():
    from prisma import Prisma
    from prisma.models import ResumePoint

    prisma_client = Prisma(auto_register=True)

    await prisma_client.connect()

    resume_points = await ResumePoint.prisma().find_many()

    print(
        f"{'':<3} | {'updatedAt':<20} | {'name':<30} | {'Interview':<10} | {'Specification':<15} | {'CompletedApp':<12} | {'Deployment':<10}"
    )
    separation_row = f"{'-' * 3}-+-{'-' * 20}-+-{'-' * 30}-+-{'-' * 10}-+-{'-' * 15}-+-{'-' * 12}-+-{'-' * 10}"
    print(separation_row)
    # Print table rows
    for i, resume_point in enumerate(resume_points):
        row = [
            str(i + 1),
            resume_point.updatedAt.isoformat().split(".")[0],
            resume_point.name,
            "✓" if resume_point.interviewId else "X",
            "✓" if resume_point.specificationId else "X",
            "✓" if resume_point.completedAppId else "X",
            "✓" if resume_point.deploymentId else "X",
        ]
        print(
            f"{row[0]:<3} | {row[1]:<20} | {row[2]:<30} | {row[3]:<10} | {row[4]:<15} | {row[5]:<12} | {row[6]:<10}"
        )
    return resume_points


@cli.command()
def resume():
    import codex.benchmark

    print("")
    resume_points = asyncio.run(get_resume_points())
    print("\n")
    case = int(input("Select index of the app you want to resume: "))

    selected_application = resume_points[case - 1]

    resume_prompt = "You can resume from, "
    resume_options = []
    valid_options = set()

    if selected_application.interviewId:
        resume_options.append("Interview (i)")
        valid_options.add("i")
        valid_options.add("I")
    if selected_application.specificationId:
        resume_options.append("Specification (s)")
        valid_options.add("s")
        valid_options.add("S")
    if selected_application.completedAppId:
        resume_options.append("Completed App (c)")
        valid_options.add("c")
        valid_options.add("C")
    if selected_application.deploymentId:
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
        print("Resuming from interview...")
        asyncio.run(
            codex.benchmark.resume_from_interview(
                selected_application.applicationId,
                selected_application.interviewId,
                selected_application,
            )
        )

    if selection in set(["s", "S"]):
        print("Resuming from specification...")
        asyncio.run(
            codex.benchmark.resume_from_specification(
                selected_application.applicationId,
                selected_application.specificationId,
                selected_application,
            )
        )

    if selection in set(["c", "C"]):
        print("Resuming from completed app...")
        asyncio.run(
            codex.benchmark.resume_from_completed_app(
                selected_application.applicationId,
                selected_application.completedAppId,
                selected_application,
            )
        )

    if selection in set(["d", "D"]):
        print("Resuming from deployment...")
        asyncio.run(
            codex.benchmark.resume_from_deployment(
                selected_application.applicationId, selected_application.deploymentId
            )
        )


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
