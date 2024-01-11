import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel

class ExecutionPath(BaseModel):
    name: str
    endpoint_name: str
    description: str

class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str

logger = logging.getLogger(__name__)

model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
    model_kwargs={"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0},
).bind(**{"response_format": {"type": "json_object"}})

parser_decode_task = PydanticOutputParser(pydantic_object=ApplicationPaths)
prompt_decompose_task = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert product owner silled at decomposing user requirements into api endpoints. Thinking carefully step by step. Output the required api endpoint needed to meet the application requirement..\n##Important\nSimple applications will require a sinlge execution path.\nReply in json format:\n{format_instructions}",
        ),
        (
            "human",
            "Thinking carefully step by step.  Decompose this problem into the required api endpoints:\n{task}",
        ),
    ]
).partial(format_instructions=parser_decode_task.get_format_instructions())
chain_decompose_task = prompt_decompose_task | model | parser_decode_task