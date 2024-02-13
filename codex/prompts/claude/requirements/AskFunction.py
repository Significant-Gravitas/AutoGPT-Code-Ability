from typing import Callable


ASK_FUNCTION_AUTO = """
Human: You are a professional answer. Your answers are always well thought out and thorough, but say no more than they need to answer the question. When you answer the question, you provide your thoughts first, set off by <thoughts> tags.

Your context is: "{context}"

Your question is: "{question}"

Assistant: <thoughts>
"""

ASK_FUNCTION: Callable[[str], str] = lambda x: input(x)
