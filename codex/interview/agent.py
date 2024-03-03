# Task Breakdown Micro Agent
import asyncio
import logging

from codex.common.ai_block import Identifiers, Tool
from codex.interview.blocks.ai_interview import InterviewBlock
from codex.interview.choose_tool import use_tool
from codex.interview.database import _create_interview_testing_only, create_interview
from codex.interview.hardcoded import (
    appointment_optimization_interview,
    availability_checker_interview,
    calendar_booking_system,
    distance_calculator_interview,
    inventory_mgmt_system,
    invoice_generator_interview,
    invoice_payment_tracking,
    profile_management,
)
from codex.interview.model import (
    Interview,
    InterviewMessage,
    InterviewMessageOptionalId,
    InterviewMessageUse,
    InterviewMessageWithResponse,
    InterviewMessageWithResponseOptionalId,
    NextStepResponse,
)
from codex.requirements.model import ExampleTask

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

    # convert all InterviewMessageWithResponseOptionalId to InterviewMessageWithResponse
    new_mem = []
    for i in memory:
        if isinstance(i, InterviewMessageWithResponseOptionalId):
            new_mem.append(
                InterviewMessageWithResponse(
                    id=i.id, tool=i.tool, content=i.content, response=i.response
                )
            )
        else:
            new_mem.append(i)
    memory = new_mem

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
            finished_text=(finish_response.content, finish_response.response),
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


def hardcoded_interview(task: ExampleTask) -> Interview:
    """
    This will take the application name and return the manually
    defined requirements for the application in the correct format
    """
    logger.warning("⚠️ Using hardcoded requirements")
    match task:
        case ExampleTask.AVAILABILITY_CHECKER:
            return availability_checker_interview()
        case ExampleTask.INVOICE_GENERATOR:
            return invoice_generator_interview()
        case ExampleTask.APPOINTMENT_OPTIMIZATION_TOOL:
            return appointment_optimization_interview()
        case ExampleTask.DISTANCE_CALCULATOR:
            return distance_calculator_interview()
        case ExampleTask.PROFILE_MANAGEMENT_SYSTEM:
            return profile_management()
        case ExampleTask.CALENDAR_BOOKING_SYSTEM:
            return calendar_booking_system()
        case ExampleTask.INVENTORY_MANAGEMENT_SYSTEM:
            return inventory_mgmt_system()
        case ExampleTask.INVOICING_AND_PAYMENT_TRACKING_SYSTEM:
            return invoice_payment_tracking()
        case _:
            raise NotImplementedError(f"Task {task} not implemented")


async def populate_database_interviews():
    from codex.api_model import Identifiers
    from codex.common.test_const import (
        app_id_1,
        app_id_2,
        app_id_3,
        app_id_4,
        app_id_5,
        app_id_6,
        app_id_7,
        app_id_8,
        identifier_1,
    )

    ids = identifier_1

    for task in list(ExampleTask):
        app_id = ExampleTask.get_app_id(task)
        interview_id = ExampleTask.get_interview_id(task)
        print(f"Creating Interview for {task}, with app_id {app_id}")
        interview = hardcoded_interview(task)
        ids.app_id = app_id
        print(ids)
        await _create_interview_testing_only(ids, interview, id=interview_id)


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