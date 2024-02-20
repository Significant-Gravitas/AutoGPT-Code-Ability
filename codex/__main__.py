import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import aiohttp
import click
from dotenv import load_dotenv
from regex import P

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
        return response


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
    setup_logging(local=os.environ.get("ENV", "CLOUD").lower() == "local")
    cli()
