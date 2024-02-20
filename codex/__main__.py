import asyncio
import io
import os
import shutil
import zipfile

import aiohttp
import click
from dotenv import load_dotenv

import codex.common.test_const as test_const
from codex.common.logging_config import setup_logging


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

    spec = await get_latest_specification(user_id, app_id)
    spec_id = spec.id
    print(f"Fetching deliverable for {spec.name}")
    url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/"
    async with session.post(url) as response:
        try:
            data = await response.json()
            deliverable_id = data["id"]
            deploy_url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
            async with session.post(deploy_url) as dresponse:
                deploy_data = await dresponse.json()
                deployment_id = deploy_data["deployment"]["id"]
                deployment_file_name = deploy_data["deployment"]["file_name"]

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

                click.echo(f"Downloaded and extracted: {extracted_folder}")

                return deploy_data
        except Exception as e:
            click.echo(f"Error fetching deliverable: {e}")
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
        ]
        results = await asyncio.gather(*tasks)
        print(results)
    await client.disconnect()


@cli.command()
def benchmark():
    """Run the benchmark tests"""
    asyncio.run(run_benchmark())


@cli.command()
def serve() -> None:
    import uvicorn

    reload = os.environ.get("ENV", "CLOUD").lower() == "local"
    log_level = "debug" if reload else "info"
    uvicorn.run(
        "codex.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=reload,
        log_level=log_level,
    )


if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    cli()
