import logging
from enum import Enum
from typing import List, Optional

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.pydantic_v1 import BaseModel, validator
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-1106-preview",
    max_tokens=4095,
    model_kwargs={"top_p": 1, "frequency_penalty": 0, "presence_penalty": 0},
).bind(**{"response_format": {"type": "json_object"}})


class Param(BaseModel):
    param_type: str
    name: str
    description: str

    @validator("param_type")
    def check_param_type(cls, v):
        basic_types = {
            "bool",
            "int",
            "float",
            "complex",
            "str",
            "bytes",
            "tuple",
            "list",
            "dict",
            "set",
            "frozenset",
        }

        # Check if it's a basic type
        if v in basic_types:
            return v

        # Check for container types like list[int]
        if v.startswith("list[") or v.startswith("set[") or v.startswith("tuple["):
            contained_type = v.split("[")[1].rstrip("]")
            if contained_type in basic_types:
                return v

        raise ValueError(
            f"param_type must be one of {basic_types}, or a container of these types"
        )


class NodeTypeEnum(Enum):
    START = "start"
    FOREACH = "forEach"
    IF = "if"
    ACTION = "action"
    END = "end"


class ElseIf(BaseModel):
    python_condition: str
    true_next_node_id: Optional[str]  # Reference to the node's name


class NodeDef(BaseModel):
    id: str
    node_type: NodeTypeEnum
    description: str
    inputs: Optional[List[Param]]
    outputs: Optional[List[Param]]
    # Unique fields for different node types with string references
    next_node_id: Optional[str] = None

    python_if_condition: Optional[str] = None
    true_next_node_id: Optional[str] = None
    elifs: Optional[List[ElseIf]] = None
    false_next_node_id: Optional[str] = None

    for_each_collection_param_name: Optional[str] = None
    for_each_next_node_id: Optional[str] = None

    @validator("next_node_id", always=True)
    def validate_next_node_id(cls, v, values, **kwargs):
        if (
            values.get("node_type")
            in [NodeTypeEnum.START, NodeTypeEnum.ACTION, NodeTypeEnum.FOREACH]
            and not v
        ):
            raise ValueError(f'{values["node_type"]} node must have a next_node_id')
        if values.get("node_type") in [NodeTypeEnum.END, NodeTypeEnum.IF] and v:
            raise ValueError(f'{values["node_type"]} node must not have a next_node_id')
        return v

    @validator("inputs", always=True)
    def validate_inputs(cls, v, values, **kwargs):
        if values.get("node_type") != NodeTypeEnum.START.value and not v:
            raise ValueError(f'{values["node_type"]} must have input parameters')
        return v

    @validator("outputs", always=True)
    def validate_outputs(cls, v, values, **kwargs):
        if values.get("node_type") == NodeTypeEnum.END.value and v:
            raise ValueError("End node must not have output parameters")
        if (
            values.get("node_type")
            in [
                NodeTypeEnum.ACTION.value,
                NodeTypeEnum.FOREACH.value,
                NodeTypeEnum.START.value,
            ]
            and not v
        ):
            raise ValueError(f'{values["node_type"]} must have output parameters')
        return v

    @validator("true_next_node_id", "false_next_node_id", always=True)
    def validate_if_node(cls, v, values, **kwargs):
        if values.get("node_type") == NodeTypeEnum.IF.value and not v:
            raise ValueError(
                "IF node must have if condition and true/false next node ids"
            )
        if values.get("node_type") != NodeTypeEnum.IF.value and v:
            raise ValueError(
                "Only IF node can have if condition and true/false next node ids"
            )
        return v

    @validator("elifs", always=True)
    def validate_elif(cls, v, values, **kwargs):
        if values.get("node_type") != NodeTypeEnum.IF.value and v:
            raise ValueError("Only IF node can have elifs")
        return v

    @validator("for_each_collection_param_name", "for_each_next_node_id", always=True)
    def validate_for_each_node(cls, v, values, **kwargs):
        if values.get("node_type") == NodeTypeEnum.FOREACH.value and not v:
            raise ValueError("FOR EACH node must have a collection param name")
        return v

    class Config:
        use_enum_values = True


class NodeGraph(BaseModel):
    nodes: List[NodeDef]

    @validator("nodes")
    def validate_nodes(cls, v):
        ids = []
        
        for node in v:
            if node.next_node_id and node.next_node_id not in ids:
                raise ValueError(
                    f"Node {node.id} has a next_node_id that does not exist: {node.next_node_id}"
                )
            if node.true_next_node_id and node.true_next_node_id not in ids:
                raise ValueError(
                    f"Node {node.id} has a true_next_node_id that does not exist: {node.true_next_node_id}"
                )
            if node.false_next_node_id and node.false_next_node_id not in ids:
                raise ValueError(
                    f"Node {node.id} has a false_next_node_id that does not exist: {node.false_next_node_id}"
                )
            if node.for_each_next_node_id and node.for_each_next_node_id not in ids:
                raise ValueError(
                    f"Node {node.id} has a for_each_next_node_id that does not exist: {node.for_each_next_node_id}"
                )
            if node.elifs:
                for elif_ in node.elifs:
                    if elif_.true_next_node_id and elif_.true_next_node_id not in ids:
                        raise ValueError(
                            f"Node {node.id} has an elif with a true_next_node_id that does not exist: {elif_.true_next_node_id}"
                        )
            return v



parser_generate_execution_graph = PydanticOutputParser(pydantic_object=NodeGraph)
prompt_generate_execution_graph = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `start` node with `request` in the name it represents a request object and only has output params. The last step is a `end` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n\n# Important:\n for param_type use only these primitive types - bool, int, float, complex, str, bytes, tuple, list, dict, set, frozenset.\n node names are in python function name format\n There must be only 1 start node and 1 end node.",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}. Do not call any nodes with the same name as the endpoint: {graph_name}",
        ),
        (
            "human",
            "Thinking carefully step by step. Ouput the steps as nodes for the api route ensuring output paraameter names of a node match the input parameter names needed by following nodes:\n{api_route}\n# Important:\n The the node definitions for all node_id's used must be in the graph",
        ),
    ]
).partial(format_instructions=parser_generate_execution_graph.get_format_instructions())


# @retry(wait=wait_none(), stop=stop_after_attempt(3))
def chain_generate_execution_graph(application_context, path, path_name):
    chain = prompt_generate_execution_graph | model | parser_generate_execution_graph
    return chain.invoke(
        {
            "application_context": application_context,
            "api_route": path,
            "graph_name": path_name,
        }
    )
