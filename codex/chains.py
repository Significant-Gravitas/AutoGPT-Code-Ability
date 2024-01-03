from typing import List, Optional

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel


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


class InputParameter(BaseModel):
    param_type: str
    name: str
    description: str
    optional: bool


class OutputParameter(BaseModel):
    param_type: str
    name: str
    description: str
    optional: bool


class NodeDefinition(BaseModel):
    name: str
    description: str
    input_params: Optional[List[InputParameter]]
    output_params: Optional[List[OutputParameter]]
    required_packages: List[str]


class NodeGraph(BaseModel):
    nodes: List[NodeDefinition]


model = ChatOpenAI(
    temperature=0,
    model="gpt-4-1106-preview",
)

######################
# Decompose task     #
######################

parser_decode_task = JsonOutputParser(pydantic_object=ApplicationPaths)
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

######################
# Generate graph     #
######################

parser_generate_execution_graph = JsonOutputParser(pydantic_object=NodeGraph)
prompt_generate_execution_graph = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `request` node with `request` in the name it represents a request object and only has output params. The last step is a `response` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n Note: param_type are primitive type avaliable in typing lib as in str, int List[str] etc.\n node names are in python function name format",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}",
        ),
        (
            "human",
            "Thinking carefully step by step. Ouput the steps as nodes for the api route:\n{api_route}",
        ),
    ]
).partial(
    format_instructions=parser_generate_execution_graph.get_format_instructions()
)
chain_generate_execution_graph = (
    prompt_generate_execution_graph | model | parser_generate_execution_graph
)

######################
# Select node        #
######################

parser_select_node = JsonOutputParser(pydantic_object=SelectNode)
prompt_select_node = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Your are an expect at node selection. You are to decide if one of the nodes presented to you fits the requirement.\nReply in json format: {format_instructions}\n Note: if no node matches the requirement reply with `new` as the node_id.",
        ),
        (
            "human",
            "Thinking carefully step by step. Select a node if it meets the requirement.\n# Nodes\n{ndoes}\n# Requirement\n{requirement}",
        ),
    ]
).partial(format_instructions=parser_select_node.get_format_instructions())
chain_select_from_possible_nodes = (
    prompt_select_node | model | parser_select_node
)

##########################
# Check node complexity  #
##########################

parser_check_node_complexity = JsonOutputParser(
    pydantic_object=CheckComplexity
)

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
).partial(
    format_instructions=parser_check_node_complexity.get_format_instructions()
)

chain_check_node_complexity = (
    prompt_check_node_complexity | model | parser_check_node_complexity
)


######################
# Decompose Node     #
######################

parser_decompose_node = JsonOutputParser(pydantic_object=NodeGraph)
prompt_decompose_node = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `request` node with `request` in the name it represents a request object and only has output params. The last step is a `response` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n Note: param_type are primitive type avaliable in typing lib as in str, int List[str] etc.\n node names are in python function name format",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}",
        ),
        (
            "human",
            "Thinking carefully step by step. Decompose this complex node into a series of simpliar steps, creating a new node graph. The new graph's request is the inputs for this node and response is the outputs of this node. Output the nodes needed to implement this complex node:\n{node}",
        ),
    ]
).partial(format_instructions=parser_decompose_node.get_format_instructions())
chain_decompose_node = prompt_decompose_node | model | parser_decompose_node

######################
# Write Node         #
######################


def _sanitize_output(text: str):
    _, after = text.split("```python")
    return after.split("```")[0]


template = """You are an expect python developer. Write the python code to implement the node.
Included error handling, comments and type hints.

Return only python code in Markdown format, e.g.:

```python
....
```"""

parser_write_node = StrOutputParser()
prompt_write_node = ChatPromptTemplate.from_messages(
    [
        ("system", template),
        ("human", "Write the code for the following node {node}"),
    ]
)
chain_write_node = (
    prompt_write_node | model | parser_write_node | _sanitize_output
)
