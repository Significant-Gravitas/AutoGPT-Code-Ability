# Task Breakdown Micro Agent
import asyncio
import logging
from typing import Callable, Optional

from codex.common.ai_block import Identifiers
from codex.requirements.blocks.interview.ai_ask import AskBlock
from codex.requirements.blocks.interview.ai_finish import FinishBlock
from codex.requirements.blocks.interview.ai_interview import InterviewBlock
from codex.requirements.blocks.interview.ai_search import SearchBlock
from codex.requirements.choose_tool import use_tool
from codex.requirements.model import (
    InterviewMessageUse,
    InterviewMessageWithResponse,
    Tool,
)

logger = logging.getLogger(__name__)


async def gather_task_info_loop(
    task: str, ids: Identifiers, ask_callback: Optional[Callable[..., str]] = None
) -> tuple[str, list[InterviewMessageWithResponse]]:
    tools: list[Tool] = [
        Tool(
            name="ask",
            description="ask the user a question",
            func=ask_callback,
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

    memory: list[InterviewMessageWithResponse] = []
    while True:
        interview_start = InterviewBlock()
        running_message: InterviewMessageUse = await interview_start.invoke(
            ids=ids,
            invoke_params={
                "task": task,
                "tools": {tool.name: tool.description for tool in tools},
                "memory": memory,
            },
        )

        # async handle for each item in running_message.uses
        results: list[InterviewMessageWithResponse] = await asyncio.gather(
            *[
                use_tool(input=i, available_tools=tools, ids=ids, memory=memory)
                for i in running_message.uses
                if i.tool == "ask"
            ]
        )

        for result in results:
            logging.debug(f"{result.tool} : {result.content} : {result.response}")
            memory.append(result)

        results: list[InterviewMessageWithResponse] = await asyncio.gather(
            *[
                use_tool(input=i, available_tools=tools, ids=ids, memory=memory)
                for i in running_message.uses
                if i.tool == "search"
            ]
        )

        for result in results:
            logging.info(f"{result.tool} : {result.content} : {result.response}")
            memory.append(result)

        if (
            any(_.tool == "finished" for _ in running_message.uses)
            and len(running_message.uses) == 1
        ):
            results: list[InterviewMessageWithResponse] = await asyncio.gather(
                *[
                    use_tool(input=i, available_tools=tools, ids=ids, memory=memory)
                    for i in running_message.uses
                    if i.tool == "finished"
                ]
            )

            for result in results:
                logging.info(f"{result.tool} : {result.content} : {result.response}")
                memory.append(result)

            # if there is a finished message, return the summary from that memory.content and the memory
            for item in memory:
                if item.tool == "finished":
                    return item.content, memory
        else:
            logging.warning("Tried to finish with pending questions.")
            continue


if __name__ == "__main__":
    from asyncio import run

    from openai import AsyncOpenAI
    from prisma import Prisma

    from codex.common.test_const import identifier_1

    ids = identifier_1
    db_client = Prisma(auto_register=True)
    oai = AsyncOpenAI()

    async def main():
        await db_client.connect()
        response, memory = await gather_task_info_loop(
            task="I need to make a website",
            ids=ids,
        )
        logger.info(response)
        await db_client.disconnect()
        return response, memory

    resp = run(main())
    logger.info(resp[0])
    logger.info(resp[1])
