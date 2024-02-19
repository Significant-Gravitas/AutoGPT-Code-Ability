import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import aiohttp
import click
from dotenv import load_dotenv

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


async def fetch_deliverable(session, user_id, app_id, spec_id):
    print(f"Fetching deliverable for {user_id=}, {app_id=}, {spec_id=}")
    url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/"
    async with session.post(url) as response:
        return response


async def run_benchmark():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_deliverable(session, 1, 1, 1),
            fetch_deliverable(session, 1, 2, 2),
            fetch_deliverable(session, 1, 3, 3),
            fetch_deliverable(session, 1, 4, 4),
            fetch_deliverable(session, 1, 5, 5),
        ]
        results = await asyncio.gather(*tasks)
        print(results)


@cli.command()
def benchmark():
    """Run the benchmark tests"""
    asyncio.run(run_benchmark())


@cli.command()
def serve() -> None:
    import uvicorn

    from codex.app import app

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))


if __name__ == "__main__":
    load_dotenv()
    setup_logging(local=os.environ.get("ENV", "CLOUD").lower() == "local")
    cli()
