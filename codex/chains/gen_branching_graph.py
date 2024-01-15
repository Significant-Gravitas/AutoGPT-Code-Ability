import logging
from enum import Enum
from typing import List, Optional

import networkx as nx
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.pydantic_v1 import BaseModel, validator
from langchain_openai import ChatOpenAI
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_none

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
    IF = "if"
    ACTION = "action"
    END = "end"


class ElseIf(BaseModel):
    python_condition: str
    true_next_node_id: Optional[str]  # Reference to the node's name


class NodeDef(BaseModel):
    name: str
    node_type: NodeTypeEnum
    description: str
    input_params: Optional[List[Param]]
    output_params: Optional[List[Param]]
    # Unique fields for different node types with string references
    next_node_id: Optional[str] = None

    python_if_condition: Optional[str] = None
    true_next_node_id: Optional[str] = None
    elifs: Optional[List[ElseIf]] = None
    false_next_node_id: Optional[str] = None

    @validator("next_node_id", always=True)
    def validate_next_node_id(cls, v, values, **kwargs):
        if (
            values.get("node_type") in [NodeTypeEnum.START, NodeTypeEnum.ACTION]
            and not v
        ):
            raise ValueError(f'{values["node_type"]} node must have a next_node_id')
        if values.get("node_type") in [NodeTypeEnum.END, NodeTypeEnum.IF] and v:
            raise ValueError(f'{values["node_type"]} node must not have a next_node_id')
        return v

    @validator("input_params", always=True)
    def validate_inputs(cls, v, values, **kwargs):
        if values.get("node_type") != NodeTypeEnum.START.value and not v:
            raise ValueError(f'{values["node_type"]} must have input parameters')
        return v

    @validator("output_params", always=True)
    def validate_outputs(cls, v, values, **kwargs):
        if values.get("node_type") == NodeTypeEnum.END.value and v:
            raise ValueError("End node must not have output parameters")
        if (
            values.get("node_type")
            in [
                NodeTypeEnum.ACTION.value,
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

    class Config:
        use_enum_values = True


class NodeGraph(BaseModel):
    nodes: List[NodeDef]

    @staticmethod
    def from_networkx(ng: nx.DiGraph):
        sorted_nodes = list(nx.topological_sort(ng))
        nodes = []
        for node in sorted_nodes:
            nodes.append(ng.nodes[node]["node"])
        return NodeGraph(nodes=nodes)

    @validator("nodes")
    def validate_nodes(cls, v):
        ids = []
        output_params = []
        # TODO: This may need improvement
        for node in v:
            ids.append(node.name)
            if node.output_params:
                for node_output in node.output_params:
                    output_params.append(
                        f"{node_output.name}: {node_output.param_type}"
                    )

            if node.input_params:
                for input_param in node.input_params:
                    if (
                        f"{input_param.name}: {input_param.param_type}"
                        not in output_params
                    ):
                        raise ValueError(
                            f"Node {node.name} has an input parameter that is not an output parameter of a previous nodes: {input_param.name}: {input_param.param_type}\n {output_params}"
                        )

        for node in v:
            if node.next_node_id and node.next_node_id not in ids:
                raise ValueError(
                    f"Node {node.name} has a next_node_id that does not exist: {node.next_node_id}"
                )
            if node.true_next_node_id and node.true_next_node_id not in ids:
                raise ValueError(
                    f"Node {node.name} has a true_next_node_id that does not exist: {node.true_next_node_id}"
                )
            if node.false_next_node_id and node.false_next_node_id not in ids:
                raise ValueError(
                    f"Node {node.name} has a false_next_node_id that does not exist: {node.false_next_node_id}"
                )
            if node.elifs:
                for elif_ in node.elifs:
                    if elif_.true_next_node_id and elif_.true_next_node_id not in ids:
                        raise ValueError(
                            f"Node {node.name} has an elif with a true_next_node_id that does not exist: {elif_.true_next_node_id}"
                        )
            return v


example_nodes = """
Eample nodes:
# Start Node (type start):
    {
         e": "startNode1",
        "node_type": "start",
        "description": "Start of the process",
        "output_params": [
            {
                "param_type": "str",
                "name": "outputParam",
                "description": "Output parameter of start node",
            }
        ],
        "next_node_id": "actionNode1",
    }
    
# Action Node (type action):
    {
        "name": "actionNode1",
        "node_type": "action",
        "description": "Perform an action",
        "input_params": [
            {
                "param_type": "int",
                "name": "actionValue",
                "description": "An integer input for the action",
            }
        ],
        "output_params": [
            {
                "param_type": "str",
                "name": "inputParam",
                "description": "The result of the action",
            }
        ],
        "next_node_id": "ifNode1", # Not needed if it is the last node in a for each loop
    },
# If Node (type if):
    {
        "name": "ifNode1",
        "node_type": "if",
        "description": "Conditional execution",
        "input_params": [
            {
                "param_type": "int",
                "name": "inputParam",
                "description": "Input parameter for condition check",
            }
        ],
        "python_if_condition": "inputParam > 10",
        "true_next_node_id": "actionNode2",
        "elifs": [
            {"python_condition": "inputParam == 5", "true_next_node_id": "actionNode3"}
        ],
        "false_next_node_id": "endNode2",
    },
# End Node (type end):
    {
        "name": "endNode1",
        "node_type": "end",
        "description": "End of the process",
        "input_params": [
            {
                "param_type": "str",
                "name": "finalValue",
                "description": "Final input value for the end node",
            }
        ],
    },
"""

parser_generate_execution_graph = PydanticOutputParser(pydantic_object=NodeGraph)
prompt_generate_execution_graph = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `start` node with `request` in the name it represents a request object and only has output params. The last step is a `end` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n\n# Important:\n for param_type use only these primitive types - bool, int, float, complex, str, bytes, tuple, list, dict, set, frozenset.\n node names are in python function name format\n There must be only 1 start node and 1 end node.\n\n# Example Nodes\n{example_nodes}",
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


@retry(
    wait=wait_none(),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)
def chain_generate_execution_graph(application_context, path, path_name):
    chain = prompt_generate_execution_graph | model | parser_generate_execution_graph
    return chain.invoke(
        {
            "application_context": application_context,
            "api_route": path,
            "graph_name": path_name,
            "example_nodes": example_nodes,
        }
    )


parser_decompose_node = PydanticOutputParser(pydantic_object=NodeGraph)
prompt_decompose_node = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert software engineer specialised in breaking down a problem into a series of steps that can be developed by a junior developer. Each step is designed to be as generic as possible. The first step is a `start` node with `request` in the name it represents a request object and only has output params. The last step is a `end` node with `response` in the name it represents aresposne object and only has input parameters.\nReply in json format:\n{format_instructions}\n\n# Important:\n for param_type use only these primitive types - bool, int, float, complex, str, bytes, tuple, list, dict, set, frozenset.\n node names are in python function name format\n There must be only 1 start node and 1 end node.\n\n# Example Nodes\n{example_nodes}",
        ),
        (
            "human",
            "The application being developed is: \n{application_context}",
        ),
        (
            "human",
            "Thinking carefully step by step. Decompose this complex node into a series of simpliar steps, creating a new node graph. The new graph's request is the input_params for this node and response is the output_params of this node. Output the nodes needed to implement this complex node:\n{node}\n # Important:\n The the node definitions for all node_id's used must be in the graph\n\n ## THE OUTPUTS OF THE START NODE MUST MATCH THE IMPUTS OF THE COMPLEX NODE\n\n ## THE INPUTS OF THE END NODE MUST MATCH THE OUTPUTS OF THE COMPLEX NODE ",
        ),
    ]
).partial(format_instructions=parser_decompose_node.get_format_instructions())


@retry(
    wait=wait_none(),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)
def chain_decompose_node(application_context, node):
    chain = prompt_decompose_node | model | parser_decompose_node
    output = chain.invoke(
        {
            "application_context": application_context,
            "node": node,
        }
    )

    # Additional validation for Node decomposition
    start_node_outputs = set()
    end_node_inputs = set()

    for node in output.nodes:
        if node.node_type == NodeTypeEnum.START.value:
            for node_output in node.output_params:
                start_node_outputs.append(
                    f"{node_output.name}: {node_output.param_type}"
                )
        if node.node_type == NodeTypeEnum.END.value:
            for node_input in node.input_params:
                end_node_inputs.append(f"{node_input.name}: {node_input.param_type}")

    requirement_node_inputs = set()
    requirement_node_outputs = set()
    for input_param in node.input_params:
        requirement_node_inputs.append(f"{input_param.name}: {input_param.param_type}")
    for output_param in node.output_params:
        requirement_node_outputs.append(
            f"{output_param.name}: {output_param.param_type}"
        )

    if requirement_node_inputs != start_node_outputs:
        raise ValueError(
            f"Start node output_params do not match requirement node input_params: {requirement_node_inputs} != {start_node_outputs}"
        )

    if requirement_node_outputs != end_node_inputs:
        raise ValueError(
            f"End node input_params do not match requirement node output_params: {requirement_node_outputs} != {end_node_inputs}"
        )

    return output


if __name__ == "__main__":
    from codex.code_gen import pre_process_nodes

    logging.basicConfig(level=logging.INFO)

    # application_context = ApplicationPaths(
    #     application_context="Develop a small script that takes a URL as input and returns the webpage in Markdown, RST or html format. Focus on converting basic HTML tags like headings, paragraphs, and lists",
    #     execution_paths=[
    #         ExecutionPath(
    #             name="convert_web_page",
    #             endpoint_name="convert_web_page",
    #             description="Convert a webpage to markdown, rst or html format, using the if node to select the correct conversion function.",
    #             example_nodes=example_nodes,
    #         )
    #     ],
    # )

    # output = chain_generate_execution_graph(
    #     application_context, "convert_web_page", "convert_web_page"
    # )
    output = NodeGraph.parse_obj(
        {
            "nodes": [
                {
                    "name": "start_request",
                    "node_type": "start",
                    "description": "Start of the process of converting a webpage to markdown, rst or html format",
                    "input_params": None,
                    "output_params": [
                        {
                            "param_type": "str",
                            "name": "urlInput",
                            "description": "URL of webpage to convert",
                        },
                        {
                            "param_type": "str",
                            "name": "formatType",
                            "description": "Format to convert the webpage to",
                        },
                    ],
                    "next_node_id": "fetch_webpage_content",
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
                {
                    "name": "fetch_webpage_content",
                    "node_type": "action",
                    "description": "Fetch webpage content",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "urlInput",
                            "description": "URL of webpage to fetch",
                        }
                    ],
                    "output_params": [
                        {
                            "param_type": "str",
                            "name": "htmlContent",
                            "description": "HTML content of the fetched webpage",
                        }
                    ],
                    "next_node_id": "determine_conversion_path",
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
                {
                    "name": "determine_conversion_path",
                    "node_type": "if",
                    "description": "Determine conversion path based on format type",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "formatType",
                            "description": "Format to convert the webpage to",
                        }
                    ],
                    "output_params": None,
                    "next_node_id": None,
                    "python_if_condition": "formatType == 'markdown'",
                    "true_next_node_id": "convert_to_markdown",
                    "elifs": [
                        {
                            "python_condition": "formatType == 'rst'",
                            "true_next_node_id": "convert_to_rst",
                        }
                    ],
                    "false_next_node_id": "convert_to_html",
                },
                {
                    "name": "convert_to_markdown",
                    "node_type": "action",
                    "description": "Convert HTML content to Markdown format",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "htmlContent",
                            "description": "HTML content to convert",
                        }
                    ],
                    "output_params": [
                        {
                            "param_type": "str",
                            "name": "convertedContent",
                            "description": "Content converted to Markdown",
                        }
                    ],
                    "next_node_id": "return_response",
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
                {
                    "name": "convert_to_rst",
                    "node_type": "action",
                    "description": "Convert HTML content to RST format",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "htmlContent",
                            "description": "HTML content to convert",
                        }
                    ],
                    "output_params": [
                        {
                            "param_type": "str",
                            "name": "convertedContent",
                            "description": "Content converted to RST",
                        }
                    ],
                    "next_node_id": "return_response",
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
                {
                    "name": "convert_to_html",
                    "node_type": "action",
                    "description": "Prepare HTML content for return",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "htmlContent",
                            "description": "HTML content to finalize",
                        }
                    ],
                    "output_params": [
                        {
                            "param_type": "str",
                            "name": "convertedContent",
                            "description": "HTML content prepared for return",
                        }
                    ],
                    "next_node_id": "return_response",
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
                {
                    "name": "return_response",
                    "node_type": "end",
                    "description": "End of the process, return the converted content",
                    "input_params": [
                        {
                            "param_type": "str",
                            "name": "convertedContent",
                            "description": "Content that has been converted",
                        }
                    ],
                    "output_params": None,
                    "next_node_id": None,
                    "python_if_condition": None,
                    "true_next_node_id": None,
                    "elifs": None,
                    "false_next_node_id": None,
                },
            ]
        }
    )

    codeable_nodes = pre_process_nodes(output)

    import IPython

    IPython.embed()
