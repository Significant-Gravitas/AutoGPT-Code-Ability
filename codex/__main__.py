import asyncio
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import click

from codex.common.logging_config import setup_logging


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--database",
    "-d",
    default="postgres://agpt_live:bnfaHGGSDF134345@127.0.0.1/codegen",
)
def populate_db(database):
    from prisma import Prisma

    db = Prisma(database_url=database, auto_register=True)

    async def popdb():
        await db.connect()
        ###
        await db.disconnect()

    asyncio.run(popdb())


@cli.command()
def test() -> None:
    def process_app(app_name: str) -> None:
        from codex.architect.agent import create_code_graphs
        from codex.delivery.agent import compile_application
        from codex.delivery.packager import create_zip_file
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


if __name__ == "__main__":
    setup_logging(local=os.environ.get("ENV", "CLOUD").lower() == "local")
    cli()
