# Tools
import logging
from typing import Callable, Optional

from codex.common.ai_block import Indentifiers
from codex.requirements.matching import find_best_match
from codex.requirements.model import (
    InterviewMessage,
    InterviewMessageWithResponse,
    Tool,
)

logger = logging.getLogger(__name__)


async def use_tool(
    input: InterviewMessage | InterviewMessageWithResponse,
    ids: Indentifiers,
    memory: list[InterviewMessageWithResponse],
    available_tools: list[Tool],
) -> InterviewMessageWithResponse:
    # Use best match here
    match = find_best_match(
        target=input.tool, choices=[tool.name for tool in available_tools]
    )
    if match:
        best_match, similarity = match[0], match[1]
        # convert the best match back to the tool object
        tool: Tool = next(tool for tool in available_tools if tool.name == best_match)
        match best_match:
            case _:
                if tool.func:
                    if resp := tool.func(input.content):
                        return InterviewMessageWithResponse(
                            tool=input.tool, content=input.content, response=resp
                        )
                # If no function is available, use the block
                print(f"Generating Response for {tool.name}")
                block = tool.block()
                response: InterviewMessageWithResponse = await block.invoke(
                    ids=ids,
                    invoke_params={
                        "content": input.content,
                        "memory": memory,
                    },
                )
                return InterviewMessageWithResponse(
                    tool=input.tool,
                    content=input.content,
                    response=response.response,
                )

    print("No Match Found")
    return InterviewMessageWithResponse(
        tool=input.tool,
        content=input.content,
        response="No match found for tool name supplied",
    )
