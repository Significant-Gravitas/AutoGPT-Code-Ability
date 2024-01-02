from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field


class ExecutionPath(BaseModel):
    name: str
    description: str


class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str


class CheckComplexity(BaseModel):
    is_complex: bool


class SelectNode(BaseModel):
    node_id: str


model = ChatOpenAI(
    temperature=0,
    model="gpt-4-1106-preview",
    )


parser_decode_task = JsonOutputParser(pydantic_object=ApplicationPaths)
prompt_decompose_task = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert product owner silled at decomposing user requirements into api endpoints. Thinking carefully step by step. Output the required api endpoint needed to meet the application requirement..\n##Important\nSimple applications will require a sinlge execution path.\nReply in json format:\n{format_instructions}",
        ),
        (
            "human",
            "Decompose this problem into the required api endpoints:\n{task}"
        ),
    ]
).partial(
    format_instructions=parser_decode_task.get_format_instructions()
)
chain_decompose_task = prompt_decompose_task | model | parser_decode_task
print(ApplicationPaths.parse_obj(chain_decompose_task.invoke({"task":  "Develop a small script that takes a URL as input and downloads the webpage and ouptus it in Markdown format."})))

parser_generate_execution_graph = JsonOutputParser(
    pydantic_object=ApplicationPaths
)
