import asyncio
import logging
import os

import click
from dotenv import load_dotenv

import codex.debug
from codex.common.logging_config import setup_logging

logger = logging.getLogger(__name__)

load_dotenv()


@click.group()
def cli():
    pass


cli.add_command(cmd=codex.debug.debug)  # type: ignore


@cli.command()
@click.option(
    "--database",
    "-d",
    default=os.getenv("DATABASE_URL"),
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
    default=os.getenv("PORT"),
    help="Port number of the Codex server",
    type=int,
)
def benchmark(port: int = 8080):
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(run_tasks())

    loop.run_until_complete(prisma_client.disconnect())


@cli.command()
@click.option(
    "-p",
    "--port",
    default=os.getenv("PORT"),
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
    loop = asyncio.new_event_loop()
    loop.run_until_complete(
        codex.runner.run_task(
            task_name=task.value,
            task_description=ExampleTask.get_task_description(task),
            user_id=codex.common.test_const.user_id_1,
            prisma_client=prisma_client,
            base_url=base_url,
        )
    )
    loop.run_until_complete(prisma_client.disconnect())


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


@cli.command()
@click.option(
    "--port",
    "-p",
    default=os.getenv("PORT"),
    help="Port number of the Codex server",
    type=int,
)
def resume(port: int):
    import prisma

    import codex.debug
    import codex.runner

    base_url = f"http://127.0.0.1:{port}/api/v1"
    prisma_client = prisma.Prisma(auto_register=True)
    print("")
    loop = asyncio.new_event_loop()
    resume_points = loop.run_until_complete(
        codex.debug.get_resume_points(prisma_client)
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

    loop.run_until_complete(
        codex.runner.resume(
            step=step,
            resume_point=selected_resume_point,
            prisma_client=prisma_client,
            base_url=base_url,
        )
    )
    loop.run_until_complete(prisma_client.disconnect())


@cli.command()
def serve() -> None:
    import uvicorn

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.exec_external_tool import setup_if_required

    OpenAIChatClient.configure({})

    logger.info("Setting up code analysis tools...")
    initial_setup = setup_if_required()
    asyncio.get_event_loop().run_until_complete(initial_setup)

    logger.info("Starting server...")
    uvicorn.run(
        app="codex.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    setup_logging()
    cli()
