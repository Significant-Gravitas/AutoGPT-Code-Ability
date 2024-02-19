import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

import click

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


@cli.command()
def serve() -> None:
    import uvicorn

    from codex.app import app

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))


if __name__ == "__main__":
    load_dotenv()
    setup_logging(local=os.environ.get("ENV", "CLOUD").lower() == "local")
    cli()
