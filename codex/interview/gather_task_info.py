# Task Breakdown Micro Agent
import asyncio
import logging

from codex.common.ai_block import Identifiers, Tool
from codex.interview.blocks.ai_interview import InterviewBlock
from codex.interview.choose_tool import use_tool
from codex.interview.model import (
    InterviewMessage,
    InterviewMessageOptionalId,
    InterviewMessageUse,
    InterviewMessageWithResponse,
    NextStepResponse,
)

logger = logging.getLogger(__name__)


async def process_pending_questions_with_ids(
    pending: list[InterviewMessage],
    tools: list[Tool],
    memory: list[InterviewMessageWithResponse],
    ids: Identifiers,
) -> list[InterviewMessageWithResponse]:
    pending_with_ids = []
    for i in pending:
        pending_with_ids.append(
            use_tool(
                input=InterviewMessageOptionalId(
                    id=i.id, tool=i.tool, content=i.content
                ),
                available_tools=tools,
                ids=ids,
                memory=memory,
            )
        )
    return await asyncio.gather(*pending_with_ids)


async def next_step(
    task: str,
    ids: Identifiers,
    memory: list[InterviewMessage | InterviewMessageWithResponse] = [],
    tools: list[Tool] = [],
) -> NextStepResponse:
    # if there is pending questions, answer them using the blocks

    ask_responses = await process_pending_questions_with_ids(
        pending=[
            i
            for i in memory
            if i.tool == "ask" and not isinstance(i, InterviewMessageWithResponse)
        ],
        tools=tools,
        memory=[x for x in memory if isinstance(x, InterviewMessageWithResponse)],
        ids=ids,
    )
    # remove all memory that was used to ask questions
    memory_removals = [
        i
        for i in memory
        if i.tool == "ask" and not isinstance(i, InterviewMessageWithResponse)
    ]
    for removal in memory_removals:
        memory.remove(removal)
    # add the responses to the memory
    memory.extend(ask_responses)
    search_responses = await process_pending_questions_with_ids(
        pending=[
            i
            for i in memory
            if i.tool == "search" and not isinstance(i, InterviewMessageWithResponse)
        ],
        tools=tools,
        memory=[x for x in memory if isinstance(x, InterviewMessageWithResponse)],
        ids=ids,
    )
    # remove all memory that was used to search
    memory_removals = [
        i
        for i in memory
        if i.tool == "search" and not isinstance(i, InterviewMessageWithResponse)
    ]
    for removal in memory_removals:
        memory.remove(removal)
    # add the responses to the memory
    memory.extend(search_responses)

    # all questions answered, start the interview
    interview_start = InterviewBlock()
    running_message: InterviewMessageUse = await interview_start.invoke(
        ids=ids,
        invoke_params={
            "task": task,
            "tools": {tool.name: tool.description for tool in tools},
            "memory": memory,
        },
    )

    # if there is only a finished message, return next reponse with it set
    if (
        any(_.tool == "finished" for _ in running_message.uses)
        and len(running_message.uses) == 1
    ):
        # TODO: insert the finished message into the memory? DB?
        finished = [x for x in running_message.uses if x.tool == "finished"][0]
        finish_response = await use_tool(
            input=InterviewMessageOptionalId(
                tool=finished.tool, content=finished.content, id=None
            ),
            available_tools=tools,
            ids=ids,
            memory=[x for x in memory if isinstance(x, InterviewMessageWithResponse)],
        )

        # if there is a finished message, return the summary from that memory.content and the memory
        return NextStepResponse(
            memory=[x for x in memory if isinstance(x, InterviewMessageWithResponse)],
            questions_to_ask=[],
            finished=True,
            # this should only ever be one message
            finished_text=(finish_response.content,finish_response.response),
        )
    else:
        # Filter out the finished message if it exists, because we clearly aren't
        # finished if we have more questions to ask
        if any(_.tool == "finish" for _ in running_message.uses):
            # remove it from the list of tools
            running_message.uses = [
                use for use in running_message.uses if use.tool != "finish"
            ]
        # if there are questions to ask, return the questions and the memory
        return NextStepResponse(
            memory=[x for x in memory if isinstance(x, InterviewMessageWithResponse)],
            questions_to_ask=running_message.uses,
            finished=False,
        )


# if __name__ == "__main__":
#     from asyncio import run

#     from openai import AsyncOpenAI
#     from prisma import Prisma

#     from codex.common.test_const import identifier_1

#     ids = identifier_1
#     db_client = Prisma(auto_register=True)
#     oai = AsyncOpenAI()

#     async def main():
#         await db_client.connect()
#         response, memory = await gather_task_info_loop(
#             task="I need to make a website",
#             ids=ids,
#         )
#         logger.info(response)
#         await db_client.disconnect()
#         return response, memory

#     resp = run(main())
#     logger.info(resp[0])
#     logger.info(resp[1])
