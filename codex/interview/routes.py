import json
import logging
from typing import List

from fastapi import APIRouter, Response

import codex.database
import codex.interview.database
from codex.api_model import Identifiers, InterviewCreate, InterviewResponse
from codex.common.ai_block import Tool
from codex.interview.blocks.ai_ask import AskBlock
from codex.interview.blocks.ai_finish import FinishBlock
from codex.interview.blocks.ai_search import SearchBlock
from codex.interview.agent import next_step
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
    try:
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

    except Exception as e:
        logger.error(f"Error creating a new Interview: {e}")
        return Response(
            content=json.dumps({"error": f"Error creating a new Interview: {str(e)}"}),
            status_code=500,
            media_type="application/json",
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
        user = await codex.database.get_user(user_id)
        ids = Identifiers(
            user_id=user_id,
            app_id=app_id,
            cloud_services_id=user.cloudServicesId if user else "",
        )

        interview = await codex.interview.database.get_interview(
            user_id, app_id, interview_id
        )

        # Add Answers to questions that were answered by the user
        # TODO: check if the user answers a question that was not asked
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
                memory.append(
                    InterviewMessage(id=x.id, tool=x.tool, content=x.question)
                )

        # Take a step
        next_set = await next_step(
            task=interview.task, ids=ids, memory=memory, tools=tools
        )

        # Add the answers from the tool usage in next_step to the db
        updated_interview = await codex.interview.database.answer_questions(
            interview_id=interview_id,
            answers=[
                x
                for x in next_set.memory
                if isinstance(x, InterviewMessageWithResponse)
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
    except Exception as e:
        logger.exception(f"Error generating Interview: {e}")
        return Response(
            content=json.dumps({"error": "Error Generating Interview"}),
            status_code=500,
            media_type="application/json",
        )


@interview_router.delete("/user/{user_id}/apps/{app_id}/interview/{interview_id}")
async def delete_interview(user_id: str, app_id: str, interview_id: str):
    """
    Delete a specific interview by its ID for a given application and user.
    """
    try:
        await codex.interview.database.delete_interview(interview_id)
        return Response(
            content=json.dumps({"message": "Interview deleted successfully"}),
            status_code=200,
            media_type="application/json",
        )
    except Exception as e:
        logger.error(f"Error deleting Interview: {e}")
        return Response(
            content=json.dumps({"error": "Error deleting Interview"}),
            status_code=500,
            media_type="application/json",
        )
