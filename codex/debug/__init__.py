import asyncio
import enum

import click
import prisma
import pydantic

import codex.common.model
import codex.debug.queries


@click.group()
def debug():
    """
    Tools for debugging the codex system.
    """
    pass


class DebugObjects(enum.Enum):
    """
    Possible objects to debug.
    """

    APP = "App"
    INTERVIEW = "Interview"
    SPEC_SUMMARY = "Spec Summary"
    API_ROUTE_SPEC = "API Route Spec"
    DATABASE_SCHEMA = "Database Schema"
    FUNCTION = "Function"
    COMPILED_ROUTE = "Compiled Route"
    COMPLETED_APP = "Completed App"
    DEPLOYMENT = "Deployment"


class WhatToDebug(pydantic.BaseModel):
    """
    What to debug.
    """

    object: DebugObjects
    app_ids: codex.common.model.ResumePoint


async def get_resume_points(prisma_client) -> list[codex.common.model.ResumePoint]:
    import datetime

    if not prisma_client.is_connected():
        await prisma_client.connect()

    resume_points_list = await codex.debug.queries.fetch_application_details()
    resume_points = resume_points_list.resume_points

    print(
        "\033[92m Todays\033[0m and\033[93m yesterdays\033[0m days apps are colored:\n"
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
            "✓" if resume_point.interviewId else "X",
            "✓" if resume_point.specificationId else "X",
            "✓" if resume_point.completedAppId else "X",
            "✓" if resume_point.deploymentId else "X",
        ]
        formatted_row = f"{color_code}{row[0]:<3} | {row[1]:<20} | {row[2]:<30} | {row[3]:<10} | {row[4]:<15} | {row[5]:<12} | {row[6]:<10}\033[0m"
        print(formatted_row)
    print(
        "\n"
        + " " * 59
        + f"{resume_points_list.pagination.current_page}/{resume_points_list.pagination.total_pages}"
    )

    return resume_points


def what_to_debug():
    """
    Works out what the user would like to debug.
    """
    click.echo("What app would you like to debug?")
    click.echo("Here are the latest apps and where they got up to.")

    prisma_client = prisma.Prisma(auto_register=True)
    click.echo("")
    resume_points = asyncio.get_event_loop().run_until_complete(
        get_resume_points(prisma_client)
    )
    click.echo("\n")
    case = int(input("Select index of the app you want to debug: "))
    app = resume_points[case - 1]
    assert app is not None, "App is None"
    click.echo("Great, now what are you intestested in debugging?")
    click.echo("Here are the different objects you can inspect:")
    for i, object in enumerate(DebugObjects):
        click.echo(f"{i + 1}. {object.value}")

    case = int(input("Select index of the object you want to debug: "))
    click.echo(
        f"Okay, lets see what is going on with {app.name}'s {list(DebugObjects)[case -1].value}"
    )

    return WhatToDebug(object=list(DebugObjects)[case - 1], app_ids=app)


def print_app(
    app: prisma.models.Application, resume_point: codex.common.model.ResumePoint
):
    """
    Print the app.
    """
    click.echo(f"Name: {app.name}")
    click.echo(f"Description: {app.description}")
    click.echo(f"Created At: {app.createdAt.isoformat().split('.')[0]}")
    click.echo("-" * 40)
    click.echo("✓ Interview" if resume_point.interviewId else "X Interview")
    click.echo("✓ Specification" if resume_point.specificationId else "X Specification")
    click.echo("✓ Compiled App" if resume_point.completedAppId else "X Compiled App")
    click.echo("✓ Deployment" if resume_point.deploymentId else "X Deployment")
    click.echo("-" * 40)


async def explore_database(this: WhatToDebug):
    prisma_client = prisma.Prisma()
    await prisma_client.connect()
    match this.object:
        case DebugObjects.APP:
            app = await prisma.models.Application.prisma().find_unique(
                where={"id": this.app_ids.applicationId}
            )
            if app:
                print_app(app, this.app_ids)
        case DebugObjects.INTERVIEW:
            pass
        case DebugObjects.SPEC_SUMMARY:
            pass
        case DebugObjects.API_ROUTE_SPEC:
            pass
        case DebugObjects.DATABASE_SCHEMA:
            pass
        case DebugObjects.FUNCTION:
            pass
        case DebugObjects.COMPILED_ROUTE:
            pass
        case DebugObjects.COMPLETED_APP:
            pass
        case DebugObjects.DEPLOYMENT:
            pass
        case _:
            pass
    await prisma_client.disconnect()


@debug.command()
@click.option("--port", "-p", default=8000, help="The port to debug.")
def llmcalls(port: int):
    """
    Debug the LLM calls.
    """
    pass


@debug.command()
@click.option("--port", "-p", default=8000, help="The port to debug.")
def object(port: int):
    """
    Debug the database objects.
    """
    this = what_to_debug()
    asyncio.get_event_loop().run_until_complete(explore_database(this))

    pass
