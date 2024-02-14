import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

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

    os.environ["DATABASE_URL"] = database
    db = Prisma(auto_register=True)

    async def popdb():
        await db.connect()
        await create_test_data()
        await populate_database_specs()
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
def test() -> None:
    def process_app(app_name: str) -> None:
        from codex.architect.agent import create_code_graphs
        from codex.deploy.agent import compile_application
        from codex.deploy.packager import create_zip_file
        from codex.developer.agent import write_code_graphs
        from codex.requirements.agent import hardcoded_requirements

        out_filename = f"{app_name.replace(' ', '_').lower()}.zip"
        # Requirements agent develops the requirements for the application
        r = hardcoded_requirements(app_name)
        # Architect agent creates the code graphs for the requirements
        graphs = create_code_graphs(r)
        # Developer agent writes the code for the code graphs
        completed_graphs = write_code_graphs(graphs)
        # Delivery Agent builds the code and delivers it to the user
        application = compile_application(r, completed_graphs)
        zipfile = create_zip_file(application)
        with open(f"workspace/{out_filename}", "wb") as f:
            f.write(zipfile)

    apps = [
        "Availability Checker",
        "Invoice Generator",
        "Appointment Optimization Tool",
        "Distance Calculator",
    ]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_app, app_name) for app_name in apps]
        for future in as_completed(futures):
            future.result()  # Waiting for each future to complete, you can handle exceptions here if needed


@cli.command()
def serve() -> None:
    import uvicorn
    from codex.app import app

    uvicorn.run(app, host="0.0.0.0", port=os.environ.get("PORT", 8000))


if __name__ == "__main__":
    setup_logging(local=os.environ.get("ENV", "CLOUD").lower() == "local")
    cli()
