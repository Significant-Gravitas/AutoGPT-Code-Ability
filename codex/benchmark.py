import asyncio
import io
import logging
import os
import shutil
import zipfile
from datetime import datetime

import aiohttp
import click
from prisma.models import Deployment, ResumePoint

import codex.common.test_const as test_const
from codex.api_model import (
    InterviewMessageWithResponse,
    InterviewResponse,
    SpecificationResponse,
)
from codex.common.codex_client import CodexClient
from codex.interview.model import InterviewMessage
from codex.requirements.database import get_latest_specification
from codex.requirements.model import ExampleTask

logger = logging.getLogger(__name__)

port = os.environ.get("PORT", 8000)


async def develop_application(
    session: aiohttp.ClientSession,
    task: ExampleTask,
    user_id: str,
    app_id: str,
    resume_point: ResumePoint,
) -> dict[str, str]:
    start_time = datetime.now()
    spec = await get_latest_specification(user_id, app_id)
    spec_id = spec.id
    logger.info(f"[{task.value}] Developing the application")
    url = f"http://127.0.0.1:{port}/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/"
    async with session.post(url, timeout=1200) as response:
        try:
            creation_time = datetime.now()
            if response.status != 200:
                return {"app_name": spec.name, "status": "failed"}

            data = await response.json()

            await ResumePoint.prisma().update(
                where={"id": resume_point.id},
                data={"CompletedApp": {"connect": {"id": data["id"]}}},
            )

            deliverable_id = data["id"]
            deploy_url = f"http://127.0.0.1:{port}/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
            async with session.post(deploy_url) as dresponse:
                deploy_data = await dresponse.json()
                deployment_id = deploy_data["id"]
                deployment_file_name = deploy_data["file_name"]

                await ResumePoint.prisma().update(
                    where={"id": resume_point.id},
                    data={"Deployment": {"connect": {"id": deployment_id}}},
                )

                # Download the zip file
                download_url = f"http://127.0.0.1:{port}/api/v1/deployments/{deployment_id}/download"
                async with session.get(download_url) as download_response:
                    content = await download_response.read()
                    content = io.BytesIO(content)

                # Unzip the file
                extracted_folder = f"workspace/{deployment_file_name.split('.')[0]}"
                if os.path.exists(extracted_folder):
                    shutil.rmtree(extracted_folder)

                # Create a new directory
                if not os.path.exists(extracted_folder):
                    os.makedirs(extracted_folder)
                with zipfile.ZipFile(content, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
                end_time = datetime.now()
                deploy_data["app_name"] = spec.name
                deploy_data["status"] = "success"
                deploy_data["dev_time"] = creation_time - start_time
                deploy_data["compile_time"] = end_time - creation_time
                return deploy_data
        except Exception as e:
            logger.exception(f"[{task.value}] Error fetching deliverable: {e}")
            return {"app_name": spec.name, "status": "failed"}


async def create_requirements(
    codex_client: CodexClient, task: ExampleTask, resume_point: ResumePoint
):
    creation_time = datetime.now()

    start_interview = await codex_client.start_interview(
        name=task.value, task=ExampleTask.get_task_description(task)
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
            f"[{task.value}] Interview: questions count {len(next_interview.uses)}"
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
    interview_finish_time = datetime.now()
    logger.info(
        f"[{task.value}] Interview finished in {interview_finish_time - creation_time}"
    )
    logger.info(f"[{task.value}] Creating Specification")
    spec: SpecificationResponse = await codex_client.generate_spec()
    spec_finish_time = datetime.now()
    logger.info(
        f"[{task.value}] Specification created in {spec_finish_time - interview_finish_time}"
    )

    updated_resume_point = await ResumePoint.prisma().update(
        where={"id": resume_point.id},
        data={"Specification": {"connect": {"id": spec.id}}},
    )

    return spec


async def run_benchmark_example(
    session, client, task, user_id, skip_requirements: bool
):
    try:
        resume_point = None
        codex_client = CodexClient(
            client=client, base_url=f"http://127.0.0.1:{port}/api/v1"
        )
        await codex_client.init(codex_user_id=user_id)
        app_id = ExampleTask.get_app_id(task=task)

        if not skip_requirements:
            logger.info(f"[{task.value}] Creating requirements")
            app = await codex_client.create_app(app_name=task.value)
            resume_point = await ResumePoint.prisma().create(
                data={
                    "Application": {"connect": {"id": app_id}},
                    "User": {"connect": {"id": user_id}},
                    "name": task.value,
                }
            )
            app_id = app.id
            await create_requirements(codex_client, task, resume_point)

        if not resume_point:
            resume_point = await ResumePoint.prisma().create(
                data={
                    "Application": {"connect": {"id": app_id}},
                    "User": {"connect": {"id": user_id}},
                    "name": task.value,
                }
            )
        if not app_id:
            raise AssertionError(
                f"[{task.value}] App ID not found for task: {task.value}"
            )

        results = await develop_application(
            session, task, user_id, app_id, resume_point
        )
        return results
    except Exception as e:
        logger.exception(f"[{task.value}] Error running benchmark: {e}")
        return {"app_name": task.value, "status": "failed"}


async def run_benchmark(skip_requirements: bool, task: ExampleTask | None = None):
    from prisma import Prisma

    logger.info(f"Running benchmark - skip-requirements: {skip_requirements}")
    client = Prisma(auto_register=True)
    await client.connect()

    examples = list(ExampleTask)
    if task:
        examples = [task]
        if skip_requirements:
            assert (
                ExampleTask.get_app_id(task) is not None
            ), f"App ID not found for {task}"
    else:
        if skip_requirements:
            examples: list[ExampleTask] = [
                task
                for task in list(ExampleTask)
                if ExampleTask.get_app_id(task) is not None
            ]

    for task in examples:
        logger.info(f"Creating {task.value}")

    async with aiohttp.ClientSession() as session:
        tasks = [
            run_benchmark_example(
                session,
                client,
                task,
                test_const.user_id_1,
                skip_requirements,
            )
            for task in examples
        ]
        results = await asyncio.gather(*tasks)
        success = len([x for x in results if x and x["status"] == "success"])
        logger.info(
            click.style(
                f"Successfully created {success}/{len(tasks)} applications.",
                fg="green",
            )
        )
        results = sorted(
            results,
            key=lambda x: x["status"] == "success" if x else False,
            reverse=True,
        )
        max_app_name_length = max(len(res["app_name"]) for res in results if res)

        for res in results:
            if res:
                if res["status"] == "success":
                    logger.info(
                        click.style(
                            f"\u2713 Created: {res['app_name']:<{max_app_name_length}} in {str(res['dev_time']).split('.')[0]} and compile time: {str(res['compile_time']).split('.')[0]}",
                            fg="green",
                        )
                    )
                else:
                    logger.info(
                        click.style(f"\u2717 Failed: {res['app_name']}", fg="red")
                    )

    await client.disconnect()


async def resume_from_interview(
    app_id: str, interview_id: str, resume_point: ResumePoint
):
    if not app_id and not interview_id:
        raise ValueError(
            "You must create an app and participate in an interview before generating a spec"
        )

    url = f"http://127.0.0.1:{port}/user/{resume_point.userId}/apps/{app_id}/specs/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                timeout=3000,
                params={"interview_id": interview_id},
            ) as response:
                response.raise_for_status()
                spec_response = SpecificationResponse(**await response.json())
                await ResumePoint.prisma().update(
                    where={"id": resume_point.id},
                    data={"Specification": {"connect": {"id": spec_response.id}}},
                )
                await resume_from_specification(app_id, spec_response.id, resume_point)

    except aiohttp.ClientError as e:
        logger.exception(f"Error generating app spec: {e}")
        raise e
    except Exception as e:
        logger.exception(f"Unknown Error when trying to generate the spec: {e}")
        raise e


async def resume_from_specification(
    app_id: str, spec_id: str, resume_point: ResumePoint
):
    async with aiohttp.ClientSession() as session:
        url = f"http://127.0.0.1:{port}/api/v1/user/{resume_point.userId}/apps/{app_id}/specs/{spec_id}/deliverables/"
        async with session.post(url, timeout=1200) as response:
            if response.status != 200:
                raise AssertionError(f"Failed to create deliverable: {response.status}")

            data = await response.json()

            await ResumePoint.prisma().update(
                where={"id": resume_point.id},
                data={"CompletedApp": {"connect": {"id": data["id"]}}},
            )
            await resume_from_completed_app(app_id, data["id"], resume_point)


async def resume_from_completed_app(
    app_id: str, completed_app_id: str, resume_point: ResumePoint
):
    async with aiohttp.ClientSession() as session:
        try:
            user_id = resume_point.userId
            spec_id = resume_point.specificationId
            if not spec_id:
                spec = await get_latest_specification(user_id, app_id)
                spec_id = spec.id
            deliverable_id = completed_app_id
            deploy_url = f"http://127.0.0.1:{port}/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
            async with session.post(deploy_url) as dresponse:
                deploy_data = await dresponse.json()
                deployment_id = deploy_data["id"]
                deployment_file_name = deploy_data["file_name"]

                await ResumePoint.prisma().update(
                    where={"id": resume_point.id},
                    data={"Deployment": {"connect": {"id": deployment_id}}},
                )

                # Download the zip file
                download_url = f"http://127.0.0.1:{port}/api/v1/deployments/{deployment_id}/download"
                async with session.get(download_url) as download_response:
                    content = await download_response.read()
                    content = io.BytesIO(content)

                # Unzip the file
                extracted_folder = f"workspace/{deployment_file_name.split('.')[0]}"
                if os.path.exists(extracted_folder):
                    shutil.rmtree(extracted_folder)

                # Create a new directory
                if not os.path.exists(extracted_folder):
                    os.makedirs(extracted_folder)
                with zipfile.ZipFile(content, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
        except Exception as e:
            logger.exception(f"Error fetching deliverable: {e}")


async def resume_from_deployment(app_id: str, deployment_id: str):
    async with aiohttp.ClientSession() as session:
        deployment = await Deployment.prisma().find_first_or_raise(
            where={"id": deployment_id}
        )
        deployment_file_name = deployment.fileName
        # Download the zip file
        download_url = (
            f"http://127.0.0.1:{port}/api/v1/deployments/{deployment_id}/download"
        )
        async with session.get(download_url) as download_response:
            content = await download_response.read()
            content = io.BytesIO(content)

        # Unzip the file
        extracted_folder = f"workspace/{deployment_file_name.split('.')[0]}"
        if os.path.exists(extracted_folder):
            shutil.rmtree(extracted_folder)

        # Create a new directory
        if not os.path.exists(extracted_folder):
            os.makedirs(extracted_folder)
        with zipfile.ZipFile(content, "r") as zip_ref:
            zip_ref.extractall(extracted_folder)
