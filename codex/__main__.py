import asyncio
import io
import logging
import os
import shutil
import zipfile
from datetime import datetime

import aiohttp
import click
from dotenv import load_dotenv

import codex.common.test_const as test_const
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
    from codex.requirements.agent import populate_database_specs

    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"] or database
    db = Prisma(auto_register=True)

    async def popdb():
        await db.connect()
        await create_test_data()
        await populate_database_specs()
        await db.disconnect()

    asyncio.run(popdb())


async def fetch_deliverable(session, user_id, app_id):
    from codex.requirements.database import get_latest_specification

    start_time = datetime.now()
    spec = await get_latest_specification(user_id, app_id)
    spec_id = spec.id
    click.echo(f"Developing the application for {spec.name}")
    url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/"
    async with session.post(url, timeout=1200) as response:
        try:
            creation_time = datetime.now()
            if response.status != 200:
                click.echo(f"\033[91mFailed creation for {spec.name}\033[0m")
                return {"app_name": spec.name, "status": "failed"}
            data = await response.json()
            deliverable_id = data["id"]
            deploy_url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
            async with session.post(deploy_url) as dresponse:
                deploy_data = await dresponse.json()
                deployment_id = deploy_data["id"]
                deployment_file_name = deploy_data["file_name"]

                # Download the zip file
                download_url = (
                    f"http://127.0.0.1:8000/api/v1/deployments/{deployment_id}/download"
                )
                async with session.get(download_url) as download_response:
                    content = await download_response.read()
                    content = io.BytesIO(content)

                # Unzip the file
                extracted_folder = f"workspace/{deployment_file_name.split('.')[0]}"
                if os.path.exists(extracted_folder):
                    shutil.rmtree(extracted_folder)

                # Create a new directory
                if not os.path.exists(extracted_folder):
                    os.makedirs(extracted_folder)
                with zipfile.ZipFile(content, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
                end_time = datetime.now()
                deploy_data["app_name"] = spec.name
                deploy_data["status"] = "success"
                deploy_data["dev_time"] = creation_time - start_time
                deploy_data["compile_time"] = end_time - creation_time
                return deploy_data
        except Exception as e:
            click.echo(f"Error fetching deliverable: {e}")
            print("Problematic URL: ", url)
            logger.exception(e)
            return


async def run_benchmark():
    from prisma import Prisma

    client = Prisma(auto_register=True)
    await client.connect()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_1),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_2),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_3),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_4),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_5),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_6),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_7),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_8),
            fetch_deliverable(session, test_const.user_id_1, test_const.app_id_11),
        ]
        results = await asyncio.gather(*tasks)
        success = len([x for x in results if x and x["status"] == "success"])
        click.echo(
            click.style(
                f"Successfully created {success}/{len(tasks)} applications.",
                fg="green",
            )
        )
        results = sorted(
            results,
            key=lambda x: x["status"] == "success" if x else False,
            reverse=True,
        )
        max_app_name_length = max(len(res["app_name"]) for res in results if res)

        for res in results:
            if res:
                if res["status"] == "success":
                    click.echo(
                        click.style(
                            f"\u2713 Created: {res['app_name']:<{max_app_name_length}} in {str(res['dev_time']).split('.')[0]} and compile time: {str(res['compile_time']).split('.')[0]}",
                            fg="green",
                        )
                    )
                else:
                    click.echo(
                        click.style(f"\u2717 Failed: {res['app_name']}", fg="red")
                    )

    await client.disconnect()


async def run_specific_benchmark(task):
    from prisma import Prisma

    from codex.requirements.model import ExampleTask

    client = Prisma(auto_register=True)
    await client.connect()
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_deliverable(
                session, test_const.user_id_1, ExampleTask.get_app_id(task)
            ),
        ]
        await asyncio.gather(*tasks)
    await client.disconnect()


@cli.command()
def benchmark():
    """Run the benchmark tests"""
    asyncio.run(run_benchmark())


@cli.command()
def example():
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
