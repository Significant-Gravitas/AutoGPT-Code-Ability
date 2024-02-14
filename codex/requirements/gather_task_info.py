# Task Breakdown Micro Agent
from typing import Callable, Optional
from anthropic import AI_PROMPT, HUMAN_PROMPT
from codex.prompts.claude.requirements.TaskIntoClarifcations import (
    TASK_INTO_MORE_INFO,
)
from codex.requirements.choose_tool import choose_tool
from codex.requirements.complete import complete_anth


def gather_task_info_loop(
    task: str, ask_callback: Optional[Callable[..., str]] = None
) -> tuple[str, str]:
    summary: str = ""
    running_message: str = TASK_INTO_MORE_INFO.format(task=task)
    for x in range(15):
        print(x)
        response = complete_anth(running_message)
        print(response)
        if not "finished:" in response.strip():
            next_message = choose_tool(
                raw_prompt=response, ask_callback=ask_callback
            )
            print(next_message)
            running_message += (
                response + HUMAN_PROMPT + next_message + AI_PROMPT
            )
        else:
            summary = response
            break
    return running_message, summary
