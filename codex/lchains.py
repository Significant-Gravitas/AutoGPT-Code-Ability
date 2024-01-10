import logging
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel

logger = logging.getLogger(__name__)


class ExecutionPath(BaseModel):
    name: str
    endpoint_name: str
    description: str


class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str


class CheckComplexity(BaseModel):
    is_complex: bool


class SelectNode(BaseModel):
    node_id: str
    input_map: Optional[Dict[str, str]]
    output_map: Optional[Dict[str, str]]

    def __str__(self) -> str:
        out = "Node ID: " + self.node_id + "\n"
        if self.input_map:
            out += "Input Map:\n"
            for k, v in self.input_map.items():
                out += f"\t{k} -> {v}\n"
        if self.output_map:
            out += "Output Map:\n"
            for k, v in self.output_map.items():
                out += f"\t{k} -> {v}\n"
        return out


class InputParameterDef(BaseModel):
    param_type: str
    name: str
    description: str
    optional: bool


class OutputParameterDef(BaseModel):
    param_type: str
    name: str
    description: str
    optional: bool


class NodeDefinition(BaseModel):
    name: str
    description: str
    input_params: Optional[List[InputParameterDef]]
    output_params: Optional[List[OutputParameterDef]]


class NodeGraph(BaseModel):
    nodes: List[NodeDefinition]


model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
    model_kwargs={"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0},
).bind(**{"response_format": {"type": "json_object"}})

code_model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
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
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `request` node with `request` in the name it represents a request object and only has output params. The last step is a `response` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n\n# Important:\n for param_type use only these primitive types - bool, int, float, complex, str, bytes, tuple, list, dict, set, frozenset.\n node names are in python function name format\n There must be only 1 node with request in the name and 1 node with response in the name",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}. Do not call any nodes with the same name as the endpoint: {graph_name}",
        ),
        (
            "human",
            "Thinking carefully step by step. Ouput the steps as nodes for the api route ensuring output paraameter names of a node match the input parameter names needed by following nodes:\n{api_route}",
        ),
    ]
).partial(format_instructions=parser_generate_execution_graph.get_format_instructions())
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
            """
Thinking carefully step by step. Select a node if it meets the requirement and provide a mapping between the selected nodes input and outputs and node specified in the requirements.

If there are no possible nodes that have all the Avaliable Input Params then reply with `new` as the node_id.

# Possible Nodes
{nodes}

# Requirement
{requirement}

# Avaliable Input Params
{avaliable_params}

# Required Output Params
{required_output_params}

## IMPORTANT!
The selected node all node inputs must be mapped to avaliable input params. If there are missing input params then the node is not a match.
The node must have all required output params. If there are missing output params then the node is not a match.
""",
        ),
    ]
).partial(format_instructions=parser_select_node.get_format_instructions())
chain_select_from_possible_nodes = prompt_select_node | model | parser_select_node

##########################
# Check node complexity  #
##########################

parser_check_node_complexity = JsonOutputParser(pydantic_object=CheckComplexity)

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


######################
# Decompose Node     #
######################

parser_decompose_node = JsonOutputParser(pydantic_object=NodeGraph)
prompt_decompose_node = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `request` node with `request` in the name it represents a request object and only has output params. The last step is a `response` node with `response` in the name it represents a resposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}",
        ),
        (
            "human",
            "Thinking carefully step by step. Decompose this complex node into a series of simpliar steps, creating a new node graph. The new graph's request is the inputs for this node and response is the outputs of this node. Output the nodes needed to implement this complex node:\n{node}\n Note:  for param_type use only primitive type avaliable in typing lib - bool, int, float, complex, str, bytes, tuple, list, dict, set, frozenset.\n node names are in python function name format.\n\n#Important\nDo not use the Any Type!",
        ),
    ]
).partial(format_instructions=parser_decompose_node.get_format_instructions())
chain_decompose_node = prompt_decompose_node | model | parser_decompose_node
