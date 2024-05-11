import asyncio
import logging
import os

import click

import codex.debug
from codex.app import db_client as prisma_client
from codex.common.logging_config import setup_logging
from codex.tests.frontend_gen_test import generate_user_interface

logger = logging.getLogger(__name__)


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

    from codex.database import create_test_data

    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"] or database
    db = prisma_client

    async def popdb():
        await db.connect()
        await create_test_data()
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
@click.option(
    "-u",
    "--base-url",
    default="http://127.0.0.1:8080/api/v1",
    help="Base URL of the Codex server",
)
@click.option(
    "-r",
    "--requirements-only",
    is_flag=True,
    default=False,
    help="Run only the requirements generation",
)
@click.option(
    "-c", "--count", default=0, help="Number of examples to run from the benchmark"
)
def benchmark(base_url: str, requirements_only: bool, count: int):
    """Run the benchmark tests"""

    import codex.common.test_const
    import codex.runner
    from codex.requirements.model import ExampleTask

    tasks = list(ExampleTask)
    if count > 0 and count < len(tasks):
        tasks = tasks[:count]
        click.echo(f"Running {count} examples from the benchmark")

    if count > len(tasks):
        click.echo(
            f"Count {count} is greater than the number of examples in the benchmark. Running all examples."
        )

    if requirements_only:
        click.echo("Running requirements generation only")

    async def run_tasks():
        user = await codex.runner.create_benchmark_user(prisma_client, base_url)

        awaitables = [
            codex.runner.run_task(
                task_name=task.value,
                task_description=ExampleTask.get_task_description(task),
                user_id=user.id,
                prisma_client=prisma_client,
                base_url=base_url,
                requirements_only=requirements_only,
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
    "-u",
    "--base-url",
    default="http://127.0.0.1:8080/api/v1",
    help="Base URL of the Codex server",
)
@click.option(
    "-r",
    "--requirements-only",
    is_flag=True,
    default=False,
    help="Run only the requirements generation",
)
def example(base_url: str, requirements_only: bool):
    import codex.common.test_const
    import codex.runner
    from codex.requirements.model import ExampleTask

    i = 1
    click.echo("Select a test case:")
    examples = list(ExampleTask)
    for task in examples:
        click.echo(f"[{i}] {task.value}")
        i += 1

    print("------")
    case = int(input("Enter number of the case to run: "))

    task = examples[case - 1]
    if requirements_only:
        click.echo("Running requirements generation only")
    loop = asyncio.new_event_loop()
    loop.run_until_complete(
        codex.runner.run_task(
            task_name=task.value,
            task_description=ExampleTask.get_task_description(task),
            user_id=codex.common.test_const.user_id_1,
            prisma_client=prisma_client,
            base_url=base_url,
            requirements_only=requirements_only,
        )
    )
    loop.run_until_complete(prisma_client.disconnect())


@cli.command()
@click.option(
    "-u",
    "--base-url",
    default="http://127.0.0.1:8080/api/v1",
    help="Base URL of the Codex server",
)
@click.option(
    "-n",
    "--name",
    default="Greetings",
    help="Name of the function",
)
@click.option(
    "-d",
    "--description",
    default="Greets the user",
    help="Description of the function",
)
@click.option(
    "-i",
    "--inputs",
    default="Users name",
    help="Inputs of the function",
)
@click.option(
    "-o",
    "--outputs",
    default="The greeting",
    help="Outputs of the function",
)
def write_function(base_url, name, description, inputs, outputs):
    import aiohttp
    from pydantic import ValidationError

    from codex.api_model import FunctionRequest
    from codex.develop.model import FunctionResponse

    async def call_codex():
        await prisma_client.connect()
        headers: dict[str, str] = {"accept": "application/json"}

        url = f"{base_url}/function/"

        req = FunctionRequest(
            name=name,
            description=description,
            inputs=inputs,
            outputs=outputs,
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=req.model_dump()
                ) as response:
                    response.raise_for_status()

                    data = await response.json()
                    print(data)
                    func = FunctionResponse.model_validate(data)
                    return func

        except aiohttp.ClientError as e:
            logger.exception(f"Error getting user: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing user: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when write function: {e}")
            raise e

    loop = asyncio.new_event_loop()
    ans = loop.run_until_complete(call_codex())
    loop.run_until_complete(prisma_client.disconnect())
    print(ans.code)


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
    "-u",
    "--base-url",
    default="http://127.0.0.1:8080/api/v1",
    help="Base URL of the Codex server",
)
def resume(base_url: str):
    import codex.debug
    import codex.runner

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
@click.option("-g", "--groq", is_flag=True, default=False, help="Run a GROQ query")
@click.option("-m", "--model", default=None, help="Override LLM to use")
def serve(groq: bool, model: str) -> None:
    import uvicorn

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.exec_external_tool import setup_if_required

    config = {}
    if model:
        config["model"] = model
    if groq:
        print("Setting up GROQ API client...")
        if not model:
            config["model"] = "llama3-70b-8192"
        config["api_key"] = os.getenv("GROQ_API_KEY")
        config["base_url"] = "https://api.groq.com/openai/v1"
        # Current limits for llama3-70b-8192 on groq
        OpenAIChatClient.configure(
            config, max_requests_per_min=1_000, max_tokens_per_min=30_000
        )
    else:
        OpenAIChatClient.configure(config)

    logger.info("Setting up code analysis tools...")
    initial_setup = setup_if_required()
    loop = asyncio.new_event_loop()
    loop.run_until_complete(initial_setup)

    logger.info("Starting server...")
    uvicorn.run(
        app="codex.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )


@cli.command()
@click.option(
    "--deliverableid",
    "-d",
    default="e3a6252d-2dec-45ad-b226-b668cb05bb0c",
    help="cloud id",
    type=str,
)
def frontend(deliverableid: str):
    """Generate a simple front-end app"""

    async def run_tasks():
        func = await generate_user_interface(deliverableid)
        assert func is not None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_tasks())


if __name__ == "__main__":
    setup_logging()
    cli()
