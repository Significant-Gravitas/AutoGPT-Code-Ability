# Tools
from typing import Callable, Optional

from codex.requirements.complete import complete_anth


def choose_tool(
    raw_prompt: str, ask_callback: Optional[Callable[..., str]] = None
) -> str:
    # TODO: DO better matching here.
    match raw_prompt.strip().lower():
        case s if s.startswith("search"):
            return complete_anth(raw_prompt, make_sendable=True)
        case s if s.startswith("ask"):
            if ask_callback:
                if resp := input(raw_prompt):
                    return resp
                else:
                    print("Generating Response for Ask")
                    return choose_tool(
                        f"search: {raw_prompt}", ask_callback=ask_callback
                    )
            else:
                print("Generating Response for Ask")
                return choose_tool(f"search: {raw_prompt}", ask_callback=ask_callback)
        case s if s.startswith("finished"):
            return "finished"
        case _:
            return ""
