import json
import logging
from typing import List

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prisma import errors as PrismaErrors

import codex.database
import codex.interview.database
from codex.api_model import Identifiers, InterviewCreate, InterviewResponse
from codex.common.ai_block import Tool
from codex.interview.agent import next_step
from codex.interview.blocks.ai_ask import AskBlock
from codex.interview.blocks.ai_finish import FinishBlock
from codex.interview.blocks.ai_search import SearchBlock
from codex.interview.model import (
    InterviewDBBase,
    InterviewMessage,
    InterviewMessageWithResponse,
)

logger = logging.getLogger(__name__)

interview_router = APIRouter(
    tags=["interview"],
)


@interview_router.post(
    "/user/{user_id}/apps/{app_id}/interview/", response_model=InterviewResponse
)
async def start_interview(
    user_id: str,
    app_id: str,
    interview_primer: InterviewCreate,
) -> Response | InterviewResponse:
    """
    Create a new Interview for a given application and user.
    """
    app = await codex.database.get_app_by_id(user_id, app_id)
    user = await codex.database.get_user(user_id)
    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )

    tools: list[Tool] = [
        Tool(
            name="ask",
            description="ask the user a question",
            # func=input? or some wrapper around it,
            block=AskBlock,
        ),
        Tool(
            name="search",
            description="search the web for information",
            # If we want to integrate opensearch or perplexity, it would be func=perplexity.search or some wrapper around it
            # func=opensearch.search,
            block=SearchBlock,
        ),
    ]

    interview = await next_step(
        task=interview_primer.task, ids=ids, memory=[], tools=tools
    )

    interview_creation = InterviewDBBase(
        project_description=interview_primer.task,
        app_name=app.name,
        questions=interview.questions_to_ask,
        finished=interview.finished,
        finished_text=interview.finished_text,
    )

    # Create db for an interview
    interview_response = await codex.interview.database.create_interview(
        ids, interview=interview_creation
    )
    return InterviewResponse(
        id=interview_response.id,
        finished=interview_response.finished,
        uses=interview_response.Questions or [],
    )


@interview_router.post(
    "/user/{user_id}/apps/{app_id}/interview/{interview_id}/next",
    response_model=InterviewResponse,
)
async def take_next_step(
    user_id: str,
    app_id: str,
    interview_id: str,
    answers: list[InterviewMessageWithResponse | InterviewMessage],
) -> Response | InterviewResponse:
    """
    Keep working through the interview until it is finished
    """
    tools: list[Tool] = [
        Tool(
            name="ask",
            description="ask the user a question",
            # func=input? or some wrapper around it,
            block=AskBlock,
        ),
        Tool(
            name="search",
            description="search the web for information",
            # If we want to integrate opensearch or perplexity, it would be func=perplexity.search or some wrapper around it
            # func=opensearch.search,
            block=SearchBlock,
        ),
        Tool(
            name="finished",
            description="finish the task and provide a comprehensive project to the user. Include the important notes from the task as well. This should be very detailed and comprehensive. Do NOT use this if there are unsettled questions.",
            block=FinishBlock,
        ),
    ]
    try:
        # Get the user
        user = await codex.database.get_user(user_id)
    except PrismaErrors.RecordNotFoundError:
        return JSONResponse(
            content=json.dumps({"error": f"User '{user_id}' not found in database."}),
            status_code=404,
        )

    # Check if the app exists
    try:
        await codex.database.get_app_by_id(user_id, app_id)
    except PrismaErrors.RecordNotFoundError:
        return JSONResponse(
            content=json.dumps({"error": f"App '{app_id}' not found in database."}),
            status_code=404,
        )

    ids = Identifiers(
        user_id=user_id,
        app_id=app_id,
        cloud_services_id=user.cloudServicesId if user else "",
    )

    # Get the interview
    try:
        interview = await codex.interview.database.get_interview(
            user_id, app_id, interview_id
        )
    except PrismaErrors.RecordNotFoundError:
        return JSONResponse(
            content=json.dumps(
                {"error": f"Interview '{interview_id}' not found in database."}
            ),
            status_code=404,
        )

    # Check if any of the question IDs in the answers don't exist in the interview
    asked_question_ids = {x.id for x in interview.Questions or []}
    answered_question_ids = {
        x.id for x in answers if isinstance(x, InterviewMessageWithResponse)
    }
    nonexistent_question_ids = answered_question_ids.difference(asked_question_ids)

    # If the user answered a question that doesn't exist in the interview, return an error
    if nonexistent_question_ids:
        error_message = f"Answered questions with IDs '{',' .join(nonexistent_question_ids)}' do not exist in the interview."
        logger.warning(msg=error_message)
        return JSONResponse(
            content=json.dumps({"error": error_message}),
            status_code=400,
        )

    # Check if the user answered a question where tool is not "ask"
    for x in answers:
        if x.tool != "ask":
            error_message = "User answered a question with a tool other than 'ask'."
            logger.warning(msg=error_message)
            # return JSONResponse(
            #     content=json.dumps({"error": error_message}),
            #     status_code=400,
            # )
            continue

    # Add Answers to any questions that were answered by the user
    updated_interview = await codex.interview.database.answer_questions(
        interview_id=interview.id,
        answers=[x for x in answers if isinstance(x, InterviewMessageWithResponse)],
    )

    # Turn the questions into a list of InterviewMessageWithResponse and InterviewMessage
    memory: List[InterviewMessage | InterviewMessageWithResponse] = []
    for x in updated_interview.Questions or []:
        if x.answer:
            memory.append(
                InterviewMessageWithResponse(
                    id=x.id, tool=x.tool, content=x.question, response=x.answer
                )
            )
        else:
            memory.append(InterviewMessage(id=x.id, tool=x.tool, content=x.question))

    # Process the next step in the interview, handling pending questions and determining if the interview is finished.
    next_set = await next_step(task=interview.task, ids=ids, memory=memory, tools=tools)

    # Add the answers from the tool usage in next_step to the db
    updated_interview = await codex.interview.database.answer_questions(
        interview_id=interview_id,
        answers=[
            x for x in next_set.memory if isinstance(x, InterviewMessageWithResponse)
        ],
    )

    # Insert new questions built by next_step into db
    updated_interview = await codex.interview.database.add_questions(
        interview_id=interview_id, questions=next_set.questions_to_ask
    )

    # If the interview is finished, add the finished content to the db
    if (
        next_set.finished
        and next_set.finished_text
        and next_set.finished_text[0]
        and next_set.finished_text[1]
    ):
        updated_interview = await codex.interview.database.finsh_interview(
            interview_id=interview_id,
            finished_content=next_set.finished_text[0],
            finished_text=next_set.finished_text[1],
        )

    return InterviewResponse(
        id=updated_interview.id,
        finished=next_set.finished,
        uses=[x for x in updated_interview.Questions or [] if not x.answer],
    )


@interview_router.delete("/user/{user_id}/apps/{app_id}/interview/{interview_id}")
async def delete_interview(user_id: str, app_id: str, interview_id: str):
    """
    Delete a specific interview by its ID for a given application and user.
    """
    await codex.interview.database.delete_interview(interview_id)
    return JSONResponse(
        content=json.dumps({"message": "Interview deleted successfully"}),
        status_code=200,
    )
