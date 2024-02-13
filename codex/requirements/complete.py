# Anthropic Completion
from enum import Enum
from typing import Type, TypeVar
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from anthropic.types import Completion as ACompletion
from pydantic import BaseModel, ValidationError

from codex.requirements.parser import parse_into_model

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


def complete_and_parse(
    prompt: str,
    return_model: Type[T],
    return_mode: ReturnMode = ReturnMode.RETURN_ONLY_LAST_ASSISTANT_REPLY,
) -> T:
    max_tries = 10
    try_counter = 1
    reply = ""
    while True:
        try:
            if try_counter >= max_tries:
                raise ValueError("You did a bad job prompting kid")
            reply: str = complete_anth(prompt, return_mode=return_mode)
            parsed: T = parse_into_model(reply, return_model)  # type: ignore
            return parsed
        except AttributeError as e:
            try_counter += 1
            print(f"{try_counter} {e} {reply}")
            pass
        except ValidationError as e:
            try_counter += 1
            print(f"{try_counter} {e} {reply}")
            pass
        except SyntaxError as e:
            try_counter += 1
            print(f"{try_counter} {e} {reply}")
            pass
        except ValueError as e:
            try_counter += 1
            if try_counter >= max_tries + 1:
                raise
            print(f"{try_counter} {e} {reply}")
        except Exception as e:
            try_counter += 1
            print(f"{try_counter} {e} {reply}")
            pass
