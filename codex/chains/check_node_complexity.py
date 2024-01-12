import logging

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel


logger = logging.getLogger(__name__)


class CheckComplexity(BaseModel):
    is_complex: bool


model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
    model_kwargs={"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0},
).bind(**{"response_format": {"type": "json_object"}})


parser_check_node_complexity = PydanticOutputParser(pydantic_object=CheckComplexity)

prompt_check_node_complexity = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer.\nReply in json format:\n{format_instructions}\nNote: reply y or n",
        ),
        (
            "human",
            "Thinking carefully step by step. Output if it is easily possible to write this function in less than 30 lines of python code without missing any implementation details. Node:\n{node}",
        ),
    ]
).partial(format_instructions=parser_check_node_complexity.get_format_instructions())

chain_check_node_complexity = (
    prompt_check_node_complexity | model | parser_check_node_complexity
)
