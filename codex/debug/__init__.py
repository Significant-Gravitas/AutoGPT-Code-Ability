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
    click.echo("Here are the different objects you can inspect:\n")
    for i, object in enumerate(DebugObjects):
        click.echo(f"{i + 1}. {object.value}")

    case = int(input("\nSelect index of the object you want to debug: "))
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
    click.echo(f"\033[92m\nName: {app.name}\033[0m")
    click.echo(f"\033[92mDescription: {app.description}\033[0m")
    click.echo(
        f"\033[92mCreated At: {app.createdAt.isoformat().split('.')[0]}\033[0m\n"
    )
    click.echo("-" * 40)
    click.echo("✓ Interview" if resume_point.interviewId else "X Interview")
    click.echo("✓ Specification" if resume_point.specificationId else "X Specification")
    click.echo("✓ Compiled App" if resume_point.completedAppId else "X Compiled App")
    click.echo("✓ Deployment" if resume_point.deploymentId else "X Deployment")
    click.echo("-" * 40)


def print_interview(interview: prisma.models.InterviewStep):
    """
    Print the interview.
    """
    click.echo("-" * 40)
    click.echo(f"\033[92mSay:\033[0m {interview.say}")
    click.echo(f"\033[92mThoughts:\033[0m {interview.thoughts}")
    click.echo(
        f"\033[92mCreated At: {interview.createdAt.isoformat().split('.')[0]}\033[0m\n"
    )
    assert interview.Features, "Features is None"
    for feature in interview.Features:
        click.echo(f"\033[93m{feature.name}\033[0m")
        click.echo(f"\033[92mFunctionality:\033[0m {feature.functionality}")
        click.echo(f"\033[92mReasoning:\033[0m {feature.reasoning}\n")
    click.echo("-" * 40)


def print_spec_summary(spec: prisma.models.Specification):
    click.echo("-" * 40)
    click.echo("\033[92mSpecification Summary\033[0m")
    click.echo("\033[92mRequested Features:\33[0m")
    assert spec.Features, "Features is None"
    for feature in spec.Features:
        click.echo(f"- {feature.name}")

    assert spec.Modules, "Modules is None"
    route_cout = sum([len(module.ApiRouteSpecs) for module in spec.Modules])  # type: ignore
    module_count = len(spec.Modules)
    click.echo(
        f"\n\033[92m{module_count} Modules\33[0m with \033[93m{route_cout} routes\33[0m\n"
    )
    click.echo("-" * 40)

    for module in spec.Modules:
        click.echo(f"\033[92m- {module.name} -\033[0m {module.description}")
        assert module.ApiRouteSpecs, "ApiRouteSpecs is None"
        for route in module.ApiRouteSpecs:
            click.echo(
                f"  - \033[93m[{route.AccessLevel}]\033[0m \033[92m{route.method}\033[0m {route.path}"
            )
        click.echo("-" * 40)


def print_api_route_details(spec: prisma.models.Specification):
    click.echo("-" * 40)
    click.echo("\033[92mAPI Route Details\033[0m")
    assert spec.Modules, "Modules is None"

    for module in spec.Modules:
        click.echo(f"\033[93m- {module.name} -\033[0m {module.description}\n")

        assert module.ApiRouteSpecs, "ApiRouteSpecs is None"
        for route in module.ApiRouteSpecs:
            click.echo(f"\n\033[93m  - {route.method}\033[0m {route.path}")
            click.echo(f"\033[92m    Description:\033[0m {route.description}")
            click.echo(f"\033[92m    Access Level:\033[0m {route.AccessLevel}")
            click.echo(
                f"\033[92m    Allowed Access Roles:\033[0m {', '.join(route.AllowedAccessRoles).upper()}"
            )
            if route.RequestObject:
                click.echo(message="\033[92m    Request Object:\033[0m")
                if route.RequestObject.Fields is not None:
                    for param in route.RequestObject.Fields:
                        click.echo(
                            f"      - {param.name}: {param.typeName}  - {param.description}"
                        )
            if route.ResponseObject:
                click.echo("\033[92m    Response Object:\033[0m")
                if route.ResponseObject.Fields is not None:
                    for param in route.ResponseObject.Fields:
                        click.echo(
                            f"      - {param.name}: {param.typeName}  - {param.description}"
                        )
        click.echo("")
        click.echo("-" * 40)
        click.echo("")


def print_database_schema(spec: prisma.models.Specification):
    click.echo("-" * 40)
    click.echo("\033[92mDetailed Database Schema\033[0m")
    assert spec.DatabaseSchema, "DatabaseSchema is None"
    assert spec.DatabaseSchema.DatabaseTables, "DatabaseTables is None"
    for table in spec.DatabaseSchema.DatabaseTables:
        click.echo(f"\n{table.definition}\n")
    click.echo("-" * 40)
    click.echo("\033[92mDatabase Schema Summary\033[0m")
    for table in spec.DatabaseSchema.DatabaseTables:
        prefix = "\033[93m- Enum: " if table.isEnum else "\033[92m- Table:"
        click.echo(f"{prefix}\033[0m {table.name}")


async def explore_database(this: WhatToDebug):
    import codex.interview.database
    import codex.requirements.database

    prisma_client = prisma.Prisma()
    await prisma_client.connect()

    assert this.app_ids.applicationId, "Application ID is None"

    match this.object:
        case DebugObjects.APP:
            app = await prisma.models.Application.prisma().find_unique_or_raise(
                where={"id": this.app_ids.applicationId}
            )
            print_app(app, this.app_ids)
        case DebugObjects.INTERVIEW:
            assert this.app_ids.interviewId, "Interview ID is None"
            click.echo(f"What to debug: {this.app_ids}")
            interview_step = await codex.interview.database.get_last_interview_step(
                interview_id=this.app_ids.interviewId, app_id=this.app_ids.applicationId
            )
            print_interview(interview_step)
        case DebugObjects.SPEC_SUMMARY:
            assert this.app_ids.specificationId, "Specification ID is None"
            assert this.app_ids.userId, "User ID is None"
            spec = await codex.requirements.database.get_specification(
                this.app_ids.userId,
                app_id=this.app_ids.applicationId,
                spec_id=this.app_ids.specificationId,
            )
            print_spec_summary(spec)
        case DebugObjects.API_ROUTE_SPEC:
            assert this.app_ids.specificationId, "Specification ID is None"
            assert this.app_ids.userId, "User ID is None"
            spec = await codex.requirements.database.get_specification(
                this.app_ids.userId,
                app_id=this.app_ids.applicationId,
                spec_id=this.app_ids.specificationId,
            )
            print_api_route_details(spec)
        case DebugObjects.DATABASE_SCHEMA:
            assert this.app_ids.specificationId, "Specification ID is None"
            assert this.app_ids.userId, "User ID is None"
            spec = await codex.requirements.database.get_specification(
                this.app_ids.userId,
                app_id=this.app_ids.applicationId,
                spec_id=this.app_ids.specificationId,
            )
            print_database_schema(spec)
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
