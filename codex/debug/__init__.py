import asyncio
import enum

import click
import prisma


@click.group()
def debug():
    """
    Tools for debugging the codex system.
    """
    pass


class PossibleObjects(enum.Enum):
    """
    Possible objects to debug.
    """

    APP = "app"
    INTERVIEW = "interview"
    SPEC_SUMMARY = "spec_summary"
    API_ROUTE_SPEC = "api_route_spec"
    DATABASE_SCHEMA = "database_schema"
    FUNCTION = "function"
    COMPILED_ROUTE = "compiled_route"
    COMLPLETED_APP = "completed_app"
    DEPLOYMENT = "deployment"


async def get_resume_points(prisma_client):
    import datetime

    import prisma.types
    from prisma.models import ResumePoint

    if not prisma_client.is_connected():
        await prisma_client.connect()

    resume_points = await ResumePoint.prisma().find_many(
        include=prisma.types.ResumePointInclude(
            Application=True,
            Interview=True,
            Specification=True,
            CompletedApp=True,
            Deployment=True,
        ),
        take=20,
        order=[{"updatedAt": "desc"}],
    )

    print(
        "\033[92m Todays\033[0m and\033[93m yesterdays\033[0m days resume points are colored:\n"
    )
    print(
        f"{'':<3} | {'updatedAt':<20} | {'name':<30} | {'Interview':<10} | {'Specification':<15} | {'CompiledAApp':<12} | {'Deployment':<10}"
    )
    separation_row = f"{'-' * 3}-+-{'-' * 20}-+-{'-' * 30}-+-{'-' * 10}-+-{'-' * 15}-+-{'-' * 12}-+-{'-' * 10}"
    print(separation_row)
    # Print table rows
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    for i, resume_point in enumerate(resume_points):
        updated_at_date = datetime.datetime.fromisoformat(
            resume_point.updatedAt.isoformat().split(".")[0]
        ).date()

        # Determine the color based on the updated date
        if updated_at_date == today:
            color_code = "\033[92m"  # Green
        elif updated_at_date == yesterday:
            color_code = "\033[93m"  # Yellow
        else:
            color_code = "\033[0m"  # Reset to default
        row = [
            str(i + 1),
            resume_point.updatedAt.isoformat().split(".")[0],
            resume_point.name[:30],
            "✓" if resume_point.Interview and resume_point.Interview.finished else "X",
            "✓" if resume_point.specificationId else "X",
            "✓" if resume_point.completedAppId else "X",
            "✓" if resume_point.deploymentId else "X",
        ]
        formatted_row = f"{color_code}{row[0]:<3} | {row[1]:<20} | {row[2]:<30} | {row[3]:<10} | {row[4]:<15} | {row[5]:<12} | {row[6]:<10}\033[0m"
        print(formatted_row)
    return resume_points


@debug.command()
@click.option("--app-id", "-a", default=None, help="The app id to debug.")
@click.option("--port", "-p", default=8000, help="The port to debug.")
def llmcalls(app_id: str, port: int):
    """
    Debug the LLM calls.
    """
    if not app_id:
        prisma_client = prisma.Prisma(auto_register=True)
        print("")
        asyncio.get_event_loop().run_until_complete(get_resume_points(prisma_client))
        print("\n")
    pass


@debug.command()
@click.option("--app-id", "-a", default=None, help="The app id to debug.")
@click.option("--port", "-p", default=8000, help="The port to debug.")
def object(app_id: str, port: int):
    """
    Debug the database objects.
    """
    if not app_id:
        prisma_client = prisma.Prisma(auto_register=True)
        print("")
        asyncio.get_event_loop().run_until_complete(get_resume_points(prisma_client))
        print("\n")
    pass
