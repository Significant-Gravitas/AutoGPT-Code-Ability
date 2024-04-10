import logging
from enum import Enum

from prisma import Prisma
from prisma.models import Application

from codex.api_model import InterviewMessageWithResponse, InterviewResponse
from codex.common.codex_client import CodexClient
from codex.common.model import ResumePoint
from codex.interview.model import InterviewMessage

logger = logging.getLogger(__name__)


class ResumeStep(Enum):
    INTERVIEW = 1
    SPECIFICATION = 2
    DEVELOPMENT = 3
    COMPILE = 4
    DOWNLOAD = 4


async def run_task(
    task_name: str,
    task_description: str,
    user_id: str,
    prisma_client: Prisma,
    base_url: str,
):
    """
    Runs a task end-to-end.

    Args:
        task_name (str): The name of the task.
        task_description (str): The description of the task.
        user_id (str): The ID of the user.
        prisma_client (Prisma): The Prisma client.
        base_url (str): The base URL.

    Returns:
        None
    """
    if not prisma_client.is_connected():
        await prisma_client.connect()
    try:
        codex_client = CodexClient(client=prisma_client, base_url=base_url)

        await codex_client.init(codex_user_id=user_id)

        app = await codex_client.create_app(
            app_name=task_name, app_description=task_description
        )

        resume_point = ResumePoint(
            name=app.name,
            updatedAt=app.updatedAt,
            userId=user_id,
            applicationId=app.id,
        )

        await run_interview(
            codex_client=codex_client,
            task_name=task_name,
            task_description=task_description,
            resume_point=resume_point,
        )

        await run_specification(
            codex_client=codex_client, task_name=task_name, resume_point=resume_point
        )

        await run_development(
            codex_client=codex_client, task_name=task_name, resume_point=resume_point
        )

        await run_compile(
            codex_client=codex_client, task_name=task_name, resume_point=resume_point
        )

    except Exception as e:
        logger.exception(f"Error running task: {e}")


async def resume(
    step: ResumeStep, resume_point: ResumePoint, prisma_client: Prisma, base_url: str
):
    """
    Resumes the task at the specified step.

    Args:
        step (ResumeStep): The step at which to resume the task.
        resume_point (ResumePoint): The resume point containing the task information.
        prisma_client (Prisma): The Prisma client used for database operations.
        base_url (str): The base URL for the Codex client.

    Raises:
        AssertionError: If the application ID is missing in the resume point.

    Returns:
        None
    """
    if not prisma_client.is_connected():
        await prisma_client.connect()
    try:
        assert resume_point.applicationId, "Application Id is required to resume"

        codex_client = CodexClient(client=prisma_client, base_url=base_url)
        await codex_client.init(
            codex_user_id=resume_point.userId,
            app_id=resume_point.applicationId,
        )

        app = await Application.prisma().find_first_or_raise(
            where={"id": resume_point.applicationId}
        )

        task_name = app.name
        task_description = app.description

        if not task_description:
            logger.error(f"Task description is missing for task: {task_name}")
            exit()

        match step:
            case ResumeStep.INTERVIEW:
                pass
            case ResumeStep.SPECIFICATION:
                codex_client.interview_id = resume_point.interviewId
            case ResumeStep.DEVELOPMENT:
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
            case ResumeStep.COMPILE:
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
                codex_client.deliverable_id = resume_point.completedAppId
            case ResumeStep.DOWNLOAD:
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
                codex_client.deliverable_id = resume_point.completedAppId
                codex_client.deployment_id = resume_point.deploymentId

        logger.info(f"Task {task_name} resumed at step {step.name}")

        if step.value <= ResumeStep.INTERVIEW.value:
            await run_interview(
                codex_client=codex_client,
                task_name=task_name,
                task_description=task_description,
                resume_point=resume_point,
            )
        if step.value <= ResumeStep.SPECIFICATION.value:
            await run_specification(
                codex_client=codex_client,
                task_name=task_name,
                resume_point=resume_point,
            )
        if step.value <= ResumeStep.DEVELOPMENT.value:
            await run_development(
                codex_client=codex_client,
                task_name=task_name,
                resume_point=resume_point,
            )

        if step.value <= ResumeStep.COMPILE.value:
            await run_compile(
                codex_client=codex_client,
                task_name=task_name,
                resume_point=resume_point,
            )


        logger.info(f"Task {task_name} finished")

    except Exception as e:
        logger.exception(f"Error resuming task: {e}")


async def run_interview(
    codex_client: CodexClient,
    task_name: str,
    task_description: str,
    resume_point: ResumePoint,
):
    """
    Runs an interview using the CodexClient.

    Args:
        codex_client (CodexClient): The CodexClient instance used to communicate with Codex.
        task_name (str): The name of the task for the interview.
        task_description (str): The description of the task for the interview.
        resume_point (ResumePoint): The resume point for the interview.

    Raises:
        Exception: If there is an error running the interview.

    Returns:
        None
    """
    try:
        start_interview = await codex_client.start_interview(
            name=task_name, task=task_description
        )

        next_interview: InterviewResponse = start_interview
        while not next_interview.finished:
            logger.info(
                f"[{task_name}] Interview: questions count {len(next_interview.uses)}"
            )
            answers: list[InterviewMessageWithResponse | InterviewMessage] = []
            for question in next_interview.uses:
                if question.tool == "search":
                    continue

                answers.append(
                    InterviewMessage(
                        id=question.id,
                        tool=question.tool,
                        content=question.question,
                    )
                )

            # Send the interview questions
            next_interview = await codex_client.interview_next(answers)
        logger.info(f"[{task_name}] Interview finished")
    except Exception as e:
        logger.exception(f"Error running interview: {e}")
        raise e


async def run_specification(
    codex_client: CodexClient, task_name: str, resume_point: ResumePoint
):
    """
    Runs the specification generation process.

    Args:
        codex_client (CodexClient): The Codex client used to generate the specification.
        task_name (str): The name of the task.
        resume_point (ResumePoint): The resume point for the task.

    Raises:
        Exception: If an error occurs during the specification generation process.
    """
    try:
        logger.info(f"[{task_name}] Creating Specification")
        await codex_client.generate_spec()
        logger.info(f"[{task_name}] Specification Created")
    except Exception as e:
        logger.exception(f"Error running specification: {e}")
        raise e


async def run_development(
    codex_client: CodexClient, task_name: str, resume_point: ResumePoint
):
    """
    Run the development process.

    Args:
        codex_client (CodexClient): The Codex client object.
        task_name (str): The name of the task.
        resume_point (ResumePoint): The resume point object.

    Raises:
        Exception: If an error occurs during the development process.

    Returns:
        None
    """
    try:
        logger.info(f"[{task_name}] Running Development")
        await codex_client.generate_deliverable()
        logger.info(f"[{task_name}] Development Finished")
    except Exception as e:
        logger.exception(f"Error running development: {e}")
        raise e


async def run_compile(
    codex_client: CodexClient, task_name: str, resume_point: ResumePoint
):
    """
    Runs the compile process for a given task.

    Args:
        codex_client (CodexClient): The Codex client instance.
        task_name (str): The name of the task.
        resume_point (ResumePoint): The resume point object.

    Raises:
        Exception: If an error occurs during the compile process.

    Returns:
        None
    """
    try:
        logger.info(f"[{task_name}] Running Compile")
        await codex_client.create_deployment()
        logger.info(f"[{task_name}] Development Compiling")
    except Exception as e:
        logger.exception(f"Error running compile: {e}")
        raise e

