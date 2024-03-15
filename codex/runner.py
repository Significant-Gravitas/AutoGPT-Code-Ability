import io
import logging
import os
import shutil
import zipfile
from enum import Enum

from prisma import Prisma
from prisma.models import Application, ResumePoint
from prisma.types import ResumePointCreateInput

from codex.api_model import (
    InterviewMessageWithResponse,
    InterviewResponse,
    SpecificationResponse,
)
from codex.common.codex_client import CodexClient
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

        resume_point = await ResumePoint.prisma().create(
            data={
                "Application": {"connect": {"id": app.id}},
                "User": {"connect": {"id": user_id}},
                "name": task_name,
            }
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

        await get_deployment(codex_client=codex_client, task_name=task_name)
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

        create_new_resume_point = False

        app = await Application.prisma().find_first_or_raise(
            where={"id": resume_point.applicationId}
        )

        task_name = app.name
        task_description = app.description

        if not task_description:
            logger.error(f"Task description is missing for task: {task_name}")
            exit()

        resume_create_data: ResumePointCreateInput | None = None

        match step:
            case ResumeStep.INTERVIEW:
                if resume_point.interviewId:
                    create_new_resume_point = True
                    resume_create_data = ResumePointCreateInput(
                        **{
                            "Application": {
                                "connect": {"id": resume_point.applicationId}
                            },
                            "User": {"connect": {"id": resume_point.userId}},
                            "name": task_name,
                        }
                    )

            case ResumeStep.SPECIFICATION:
                if resume_point.specificationId:
                    create_new_resume_point = True
                    resume_create_data = ResumePointCreateInput(
                        **{
                            "Application": {
                                "connect": {"id": resume_point.applicationId}
                            },
                            "Interview": {"connect": {"id": resume_point.interviewId}},
                            "User": {"connect": {"id": resume_point.userId}},
                            "name": task_name,
                        }
                    )
                codex_client.interview_id = resume_point.interviewId
            case ResumeStep.DEVELOPMENT:
                if resume_point.completedAppId:
                    create_new_resume_point = True
                    resume_create_data = ResumePointCreateInput(
                        **{
                            "Application": {
                                "connect": {"id": resume_point.applicationId}
                            },
                            "Interview": {"connect": {"id": resume_point.interviewId}},
                            "Specification": {
                                "connect": {"id": resume_point.specificationId}
                            },
                            "User": {"connect": {"id": resume_point.userId}},
                            "name": task_name,
                        }
                    )
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
            case ResumeStep.COMPILE:
                if resume_point.deploymentId:
                    create_new_resume_point = True
                    resume_create_data = ResumePointCreateInput(
                        **{
                            "Application": {
                                "connect": {"id": resume_point.applicationId}
                            },
                            "Interview": {"connect": {"id": resume_point.interviewId}},
                            "Specification": {
                                "connect": {"id": resume_point.specificationId}
                            },
                            "CompletedApp": {
                                "connect": {"id": resume_point.completedAppId}
                            },
                            "User": {"connect": {"id": resume_point.userId}},
                            "name": task_name,
                        }
                    )
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
                codex_client.deliverable_id = resume_point.completedAppId
            case ResumeStep.DOWNLOAD:
                codex_client.interview_id = resume_point.interviewId
                codex_client.specification_id = resume_point.specificationId
                codex_client.deliverable_id = resume_point.completedAppId
                codex_client.deployment_id = resume_point.deploymentId

        if create_new_resume_point and resume_create_data:
            resume_point = await ResumePoint.prisma().create(data=resume_create_data)

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

        if step.value <= ResumeStep.DOWNLOAD.value:
            await get_deployment(codex_client=codex_client, task_name=task_name)

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
        updated_resume_point = await ResumePoint.prisma().update(
            where={"id": resume_point.id},
            data={"Interview": {"connect": {"id": start_interview.id}}},
        )

        if updated_resume_point:
            resume_point = updated_resume_point

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
        spec: SpecificationResponse = await codex_client.generate_spec()
        updated_resume_point = await ResumePoint.prisma().update(
            where={"id": resume_point.id},
            data={"Specification": {"connect": {"id": spec.id}}},
        )
        if updated_resume_point:
            resume_point = updated_resume_point
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
        deliverable = await codex_client.generate_deliverable()
        await ResumePoint.prisma().update(
            where={"id": resume_point.id},
            data={"CompletedApp": {"connect": {"id": deliverable.id}}},
        )
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
        deployment = await codex_client.create_deployment()
        await ResumePoint.prisma().update(
            where={"id": resume_point.id},
            data={"Deployment": {"connect": {"id": deployment.id}}},
        )
        logger.info(f"[{task_name}] Development Compiling")
    except Exception as e:
        logger.exception(f"Error running compile: {e}")
        raise e


async def get_deployment(codex_client: CodexClient, task_name: str):
    """
    Downloads a zip file from the Codex client and extracts its contents to a specified folder.

    Args:
        codex_client (CodexClient): The Codex client instance.
        task_name (str): The name of the task.

    Raises:
        Exception: If there is an error downloading the file.

    Returns:
        None
    """
    try:
        logger.info(f"[{task_name}] Downloading File")
        content, file_name = await codex_client.download_zip()
        content = io.BytesIO(content)
        extracted_folder = f"workspace/{file_name.split('.')[0]}"
        if os.path.exists(extracted_folder):
            shutil.rmtree(extracted_folder)

        # Create a new directory
        if not os.path.exists(extracted_folder):
            os.makedirs(extracted_folder)
        with zipfile.ZipFile(content, "r") as zip_ref:
            zip_ref.extractall(extracted_folder)

        logger.info(f"[{task_name}] Download Complete File is in : {extracted_folder}")
    except Exception as e:
        logger.exception(f"Error downloading the file: {e}")
        raise e
        logger.exception(f"Error downloading the file: {e}")
        raise e
