# Tools
import logging

from codex.common.ai_block import Identifiers, Tool
from codex.interview.model import (
    InterviewMessageOptionalId,
    InterviewMessageWithResponse,
    InterviewMessageWithResponseOptionalId,
)
from codex.requirements.matching import find_best_match

logger = logging.getLogger(__name__)


async def use_tool(
    input: InterviewMessageOptionalId | InterviewMessageWithResponseOptionalId,
    ids: Identifiers,
    memory: list[InterviewMessageWithResponse],
    available_tools: list[Tool],
) -> InterviewMessageWithResponseOptionalId:
    # Use best match here
    match = find_best_match(
        target=input.tool, choices=[tool.name for tool in available_tools]
    )
    if match:
        best_match, _similarity = match[0], match[1]
        # convert the best match back to the tool object
        tool: Tool = next(tool for tool in available_tools if tool.name == best_match)
        match best_match:
            case _:
                if tool.func:
                    if resp := tool.func(input.content):
                        return InterviewMessageWithResponseOptionalId(
                            id=input.id,
                            tool=input.tool,
                            content=input.content,
                            response=resp,
                        )
                # If no function is available, use the block
                logger.info(f"Generating Response for {tool.name}")
                block = tool.block()
                response: InterviewMessageWithResponse = await block.invoke(
                    ids=ids,
                    invoke_params={
                        "content": input.content,
                        "memory": memory,
                    },
                )
                return InterviewMessageWithResponseOptionalId(
                    id=input.id,
                    tool=input.tool,
                    content=input.content,
                    response=response.response,
                )

    if input.tool == "finished":
        return InterviewMessageWithResponseOptionalId(
            id=input.id,
            tool=input.tool,
            content=input.content,
            response=input.content,
        )
    logger.error("No Match Found")
    return InterviewMessageWithResponseOptionalId(
        id=input.id,
        tool=input.tool,
        content=input.content,
        response="No match found for tool name supplied",
    )
