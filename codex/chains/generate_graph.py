import logging
from typing import List, Optional, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, validator
import networkx as nx
from tenacity import retry, stop_after_attempt, wait_none

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
    optional: bool

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


class NodeDefinition(BaseModel):
    name: str
    description: str
    input_params: Optional[List[Param]]
    output_params: Optional[List[Param]]


class NodeGraph(BaseModel):
    nodes: List[NodeDefinition]

    def add_node(graph: nx.DiGraph, node_name: str, node: NodeDefinition) -> bool:
        if graph.number_of_nodes() == 0:
            graph.add_node(node_name, node=node)
            return True

        if "response" not in node_name and not node.output_params:
            logger.error(f"Node {node_name} has no output parameters\n {node}")

        # Check if node's input parameters are satisfied by the existing nodes in the graph
        if node.input_params:
            input_params_needed = [
                f"{p.name}: {p.param_type}" for p in node.input_params
            ]
        else:
            input_params_needed = {}

        # Find nodes in the graph that can provide the required input parameters
        # TODO: This method requires an exact match of the variable name and type
        providers: Dict[Tuple[str, str], NodeDefinition] = {}
        for n in graph.nodes:
            existing_node: NodeDefinition = graph.nodes[n]["node"]

            if existing_node.output_params:
                for output_param in existing_node.output_params:
                    param_key = f"{output_param.name}: {output_param.param_type}"
                    if param_key in input_params_needed:
                        providers[param_key] = n

        # Check if all input parameters are available
        if len(input_params_needed) != len(providers):
            raise ValueError(
                f"Node {node_name} is missing input parameters: {input_params_needed}. Details:\n\tNode: {node}\n\tProviders: {providers}"
            )

        # Add the new node
        graph.add_node(node_name, node=node)

        # Connect the new node to its parameter providers
        for param_key, provider_node in providers.items():
            graph.add_edge(provider_node, node_name, connection_type=param_key[0])

        return True

    @validator("nodes")
    def check_nodes(cls, v):
        if len(v) == 0:
            raise ValueError("Node graph is empty")

        # Check if the first node is a request node
        if "request" not in v[0].name.lower():
            raise ValueError("Node graph does not start with a request node")
        if len(v[0].output_params) == 0:
            raise ValueError("Request node does not have output parameters")
        if len(v[0].input_params) > 0:
            raise ValueError("Request node has input parameters")

        # Check if the last node is a response node
        if "response" not in v[-1].name.lower():
            raise ValueError("Node graph does not end with a response node")
        if len(v[-1].input_params) == 0:
            raise ValueError("Response node does not have input parameters")
        if len(v[-1].output_params) > 0:
            raise ValueError("Response node has output parameters")

        # Check if all nodes are connected
        dag = nx.DiGraph()
        for node in v:
            cls.add_node(dag, node.name, node)

        return v


parser_generate_execution_graph = PydanticOutputParser(pydantic_object=NodeGraph)
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


@retry(wait=wait_none(), stop=stop_after_attempt(3))
def chain_generate_execution_graph(application_context, path, path_name):
    chain = prompt_generate_execution_graph | model | parser_generate_execution_graph
    return chain.invoke(
        {
            "application_context": application_context,
            "api_route": path,
            "graph_name": path_name,
        }
    )


parser_decompose_node = PydanticOutputParser(pydantic_object=NodeGraph)
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


@retry(wait=wait_none(), stop=stop_after_attempt(3))
def chain_decompose_node(application_context, path):
    chain = prompt_decompose_node | model | parser_decompose_node
    return chain.invoke(
        {
            "application_context": application_context,
            "node": path,
        }
    )
