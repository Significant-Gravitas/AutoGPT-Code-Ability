from typing import List, Optional
from codex.model import Node, InputParameter, OutputParameter
from codex.database import search_nodes_by_params
import logging
from openai import OpenAI
import json
from openai import OpenAI
from pydantic import BaseModel
import networkx as nx
import concurrent.futures
from codex.dag import add_node


class ExecutionPath(BaseModel):
    name: str
    description: str


class ApplicationPaths(BaseModel):
    execution_paths: List[ExecutionPath]
    application_context: str


class NodeGraph(BaseModel):
    name: str
    description: str
    nodes: List[Node]


class Application(BaseModel):
    application_context: str
    execution_paths: List[NodeGraph]


client = OpenAI()

# response = client.chat.completions.create(
#     model="gpt-4-1106-preview",
#     messages=[
#         {
#             "role": "system",
#             "content": 'Reply in json format: \n{ "nodes": [\n { "name": "node name",\n    "description", "node description",\n     "input_params": [ { "param_type": "type as in str, int List[str] etc",\n"name": "param name",\n"description": "what this param represents",\n"optional": bool\n}, ... ],\n"output_params": [ { "param_type": "type as in str, int List[str] etc",\n"name": "param name",\n"description": "what this param represents",\n"optional": bool\n}, ... ] \n},\n...\n]}\n\nThinking carefully step by step. Output the nodes needed for the execution path the user specifies. Ensuring each node is can be easily coded up by a junior developer.  The first node needs to be a request node with only output params and the last node is a response node with only input parameters\n',
#         }
#     ],
#     temperature=1,
#     max_tokens=4095,
#     top_p=1,
#     frequency_penalty=0,
#     presence_penalty=0,
#     response_format={"type": "json_object"},
# )


# Function definitions
def decompose_task(task_description: str) -> ApplicationPaths:
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": 'Reply in json format: { "execution_paths": \n[\n '
                + '{ "name": "Name of'
                + 'execution path",\n    "description", "description of the '
                + 'functionality this execution path provides"\n},\n...\n'
                + '], "application_context": "Summary of application"}\n\n'
                + "Thinking carefully step by step. Output the required "
                + "each execution path needed to meet the application "
                + "requirement where an execution path is a logic path"
                + "from request through to repsonse such as an api endpoint."
                + "Simple applications will require a sinlge execution path:",
            },
            {
                "role": "user",
                "content": task_description,
            },
        ],
        max_tokens=4095,
        response_format={"type": "json_object"},
    )
    return ApplicationPaths.model_validate(
        json.loads(response.choices[0].message.content)  # type: ignore
    )


def generate_execution_graph(execution_path: ExecutionPath) -> NodeGraph:
    """
    Takes in a single ExecutionPath and makes a request to OpenAI,
    which returns a list of nodes.
    """
    # Implement your logic here
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": 'Reply in json format: \n{ "nodes": [\n { "name": "node name",\n    "description", "node description",\n     "input_params": [ { "param_type": "type as in str, int List[str] etc",\n"name": "param name",\n"description": "what this param represents",\n"optional": bool\n}, ... ],\n"output_params": [ { "param_type": "primitive type avaliable in typing lib as in str, int List[str] etc",\n"name": "param name",\n"description": "what this param represents",\n"optional": bool\n}, ... ] \n},\n...\n]}\n\nThinking carefully step by step. Output the nodes needed for the execution path the user specifies. Ensuring each node is can be easily coded up by a junior developer.  The first node needs to be a request node with only output params and the last node is a response node with only input parameters specified which is what will be returned to the user\n',
            }
        ],
        temperature=1,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={"type": "json_object"},
    )

    ngr = NodeGraph(
        name=execution_path.name,
        description=execution_path.description,
        nodes=[],
    )
    for node in json.loads(response.choices[0].message.content)["nodes"]:
        n = Node.model_validate(node)
        n.input_params = [
            InputParameter.model_validate(param)
            for param in node["input_params"]
        ]
        n.output_params = [
            OutputParameter.model_validate(param)
            for param in node["output_params"]
        ]
        ngr.nodes.append(n)

    return ngr


def generate_execution_graphs(
    execution_paths: List[ExecutionPath],
) -> List[NodeGraph]:
    """
    Takes in a list of ExecutionPaths and processes
    each to generate execution graphs.
    """
    results: List[NodeGraph] = []
    for path in execution_paths:
        results.append(generate_execution_graph(path))
    return results
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     futures = [
    #         executor.submit(generate_execution_graph, path)
    #         for path in execution_paths
    #     ]
    #     for future in concurrent.futures.as_completed(futures):
    #         results.append(future.result())
    # return results


def build_graph(graph: NodeGraph):
    """
    Takes in a graph and returns a boolean indicating whether the graph is valid.
    """
    dag = nx.DiGraph()
    for node in graph:
        added_node = add_node(dag, node.name, node)
        if added_node and (
            "response" not in node.name or "request" not in node.name
        ):
            pass


def lookup_node(node: Node) -> List[Node]:
    """
    Takes in a node and outputs the closest matches or returns an empty list.
    """

    # Implement your logic here
    pass


def write_node(node: Node) -> str:
    """
    Takes in a node and returns a string representation of it.
    """
    # Implement your logic here
    pass


def create_server_runner(nodes: List[Node]) -> str:
    """
    Takes in a list of nodes and outputs a string to create a server runner.
    """
    # Implement your logic here
    pass


def create_cli_runner(nodes: List[Node]) -> str:
    """
    Takes in a list of nodes and outputs a string to create a CLI runner.
    """
    # Implement your logic here
    pass


if __name__ == "__main__":
    paths = decompose_task(
        "Develop a small script that takes a URL as input and downloads the webpage and ouptus it in Markdown format."
    )
    print(paths)
    node_graphs = generate_execution_graphs(paths.execution_paths)
    import IPython

    IPython.embed()
    print(paths)
