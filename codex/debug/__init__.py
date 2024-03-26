import asyncio
import click
import enum
import prisma
import pydantic

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
    object: DebugObjects | None = None
    app_id: str
    interview_id: str | None = None
    spec_id: str | None = None
    route_spec_id: str | None = None
    database_schema_id: str | None = None
    function_id: str | None = None
    compiled_route_id: str | None = None
    completed_app_id: str | None = None
    deployment_id: str | None = None
    

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
            "✓" if resume_point.Interview and resume_point.Interview.finished else "X",
            "✓" if resume_point.specificationId else "X",
            "✓" if resume_point.completedAppId else "X",
            "✓" if resume_point.deploymentId else "X",
        ]
        formatted_row = f"{color_code}{row[0]:<3} | {row[1]:<20} | {row[2]:<30} | {row[3]:<10} | {row[4]:<15} | {row[5]:<12} | {row[6]:<10}\033[0m"
        print(formatted_row)
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
    app = resume_points[case - 1] # type: ignore
    click.echo("Great, now what are you intestested in debugging?")
    click.echo("Here are the different objects you can inspect:")
    for i, object in enumerate(DebugObjects):
        click.echo(f"{i + 1}. {object.value}")
        
    case = int(input("Select index of the object you want to debug: "))
    click.echo(f"Okay, lets see what is going on with {app.name}'s {list(DebugObjects)[case -1].value}")
        
    

        
    

@debug.command()
@click.option("--port", "-p", default=8000, help="The port to debug.")
def llmcalls( port: int):
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
    what_to_debug()
    pass
