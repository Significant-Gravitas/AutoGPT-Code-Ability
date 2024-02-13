# Tools
from codex.requirements.complete import complete_anth


def choose_tool(raw_prompt: str) -> str:
    #TODO: DO better matching here. 
    match raw_prompt.strip().lower():
        case s if s.startswith("search"):
            return complete_anth(
                raw_prompt,
                make_sendable=True
            )
        case s if s.startswith("ask"):
            if resp := input(raw_prompt):
                return resp
            else:
                print("Generating Response for Ask")
                return choose_tool(f"search: {raw_prompt}")
        case s if s.startswith("finished"):
            return "finished"
        case _:
            return ""
