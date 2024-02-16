# Anthropic Completion
from enum import Enum
from typing import TypeVar

from anthropic import AI_PROMPT, HUMAN_PROMPT, Anthropic
from anthropic.types import Completion as ACompletion
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ReturnMode(Enum):
    RETURN_FULL_CONVO = "return_full_convo"
    RETURN_ONLY_LAST_ASSISTANT_REPLY = "return_only_last_assistant_reply"
    RETURN_ONLY_COMPLETION = "return_only_completion"


def complete_anth(
    prompt: str,
    make_sendable: bool = False,
    return_mode: ReturnMode = ReturnMode.RETURN_ONLY_LAST_ASSISTANT_REPLY,
    depth: int = 0,
) -> str:
    """Make sure you do your own management of including human and assistant"""
    depth = depth + 1
    if depth >= 3:
        raise ValueError(
            "Too many completions deep. This will cost you some money honey"
        )
    if make_sendable:
        sendable_prompt = f"{HUMAN_PROMPT} {prompt} {AI_PROMPT}"
    else:
        sendable_prompt = f"{prompt}"
    anthropic = Anthropic(
        api_key="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"
    )

    if not sendable_prompt.startswith("\n\n"):
        sendable_prompt = "\n\n" + sendable_prompt

    completion: ACompletion = anthropic.completions.create(
        model="claude-2.1",
        max_tokens_to_sample=1000000,
        prompt=sendable_prompt,
    )
    if completion.stop_reason == "max_tokens":
        print(completion.completion)
        continued = completion.completion + complete_anth(
            prompt=sendable_prompt + completion.completion,
            return_mode=ReturnMode.RETURN_ONLY_COMPLETION,
            depth=depth,
        )
        completion.completion = continued

    switcher = {
        ReturnMode.RETURN_FULL_CONVO: sendable_prompt + completion.completion,
        ReturnMode.RETURN_ONLY_COMPLETION: completion.completion,
        ReturnMode.RETURN_ONLY_LAST_ASSISTANT_REPLY: (
            sendable_prompt + completion.completion
        )
        .split("Assistant: ")[-1]
        .strip(),
    }
    return switcher.get(return_mode, "Invalid return mode")
