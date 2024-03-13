import asyncio
import io
import logging
import os
import shutil
import zipfile
from datetime import datetime

import aiohttp
import click

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


async def develop_application(
    session: aiohttp.ClientSession, task: ExampleTask, user_id: str, app_id: str
) -> dict[str, str]:
    start_time = datetime.now()
    spec = await get_latest_specification(user_id, app_id)
    spec_id = spec.id
    logger.info(f"[{task.value}] Developing the application")
    url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/"
    async with session.post(url, timeout=1200) as response:
        try:
            creation_time = datetime.now()
            if response.status != 200:
                return {"app_name": spec.name, "status": "failed"}
            data = await response.json()
            deliverable_id = data["id"]
            deploy_url = f"http://127.0.0.1:8000/api/v1/user/{user_id}/apps/{app_id}/specs/{spec_id}/deliverables/{deliverable_id}/deployments/"
            async with session.post(deploy_url) as dresponse:
                deploy_data = await dresponse.json()
                deployment_id = deploy_data["id"]
                deployment_file_name = deploy_data["file_name"]

                # Download the zip file
                download_url = (
                    f"http://127.0.0.1:8000/api/v1/deployments/{deployment_id}/download"
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
                end_time = datetime.now()
                deploy_data["app_name"] = spec.name
                deploy_data["status"] = "success"
                deploy_data["dev_time"] = creation_time - start_time
                deploy_data["compile_time"] = end_time - creation_time
                return deploy_data
        except Exception as e:
            logger.exception(f"[{task.value}] Error fetching deliverable: {e}")
            return {"app_name": spec.name, "status": "failed"}


async def create_requirements(codex_client: CodexClient, task: ExampleTask):
    creation_time = datetime.now()

    start_interview = await codex_client.start_interview(
        name=task.value, task=ExampleTask.get_task_description(task)
    )
    next_interview: InterviewResponse = start_interview

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
    return spec


async def run_benchmark_example(
    session, client, task, user_id, skip_requirements: bool
):
    try:
        codex_client = CodexClient(
            client=client, base_url="http://127.0.0.1:8000/api/v1"
        )
        await codex_client.init(codex_user_id=user_id)
        app_id = ExampleTask.get_app_id(task=task)

        if not skip_requirements:
            logger.info(f"[{task.value}] Creating requirements")
            app = await codex_client.create_app(app_name=task.value)
            app_id = app.id
            await create_requirements(codex_client, task)

        if not app_id:
            raise AssertionError(
                f"[{task.value}] App ID not found for task: {task.value}"
            )

        results = await develop_application(session, task, user_id, app_id)
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
