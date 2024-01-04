from typing import Dict, Tuple

import networkx as nx
import logging
from .model import Node

logger = logging.getLogger(__name__)


def add_node(graph: nx.DiGraph, node_name: str, node: Node) -> bool:
    if graph.number_of_nodes() == 0:
        graph.add_node(node_name, node=node)
        return True

    # Check if node's input parameters are satisfied by the existing nodes in the graph
    if node.input_params:
        input_params_needed = [
            f"{p.name}: {p.param_type}" for p in node.input_params
        ]
    else:
        input_params_needed = {}

    # Find nodes in the graph that can provide the required input parameters
    # TODO: This method requires an exact match of the variable name and type
    providers: Dict[Tuple[str, str], Node] = {}
    for n in graph.nodes:
        existing_node: Node = graph.nodes[n]["node"]

        assert isinstance(
            existing_node, Node
        ), f"Node {n} is not a Node object {type(existing_node)}"

        if existing_node.output_params:
            for output_param in existing_node.output_params:
                param_key = f"{output_param.name}: {output_param.param_type}"
                if param_key in input_params_needed:
                    providers[param_key] = n

    # Check if all input parameters are available
    if len(input_params_needed) != len(providers):
        raise ValueError(
            f"Node {node_name} is missing input parameters: {input_params_needed}"
        )

    # Add the new node
    graph.add_node(node_name, node=node)

    # Connect the new node to its parameter providers
    for param_key, provider_node in providers.items():
        graph.add_edge(provider_node, node_name, connection_type=param_key[0])

    return True


def compile_graph(graph: nx.DiGraph):
    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise nx.NetworkXError("Graph is not a Directed Acyclic Graph (DAG)")

    output_name_map: Dict[str, str] = {}

    python_file = ""
    graph_script = ""
    for node_name in nx.topological_sort(graph):
        node: Node = graph.nodes[node_name]["node"]
        if "request" in node_name:
            graph_script += node.request_to_code()
        elif "response" in node_name:
            graph_script += node.response_to_code(output_name_map)
        else:
            python_file += f"\n{node.code}\n"
            code, unique_output_names_map = node.to_code(output_name_map)
            output_name_map: Dict[str, str] = {
                **output_name_map,
                **unique_output_names_map,
            }
            graph_script += f"{code}\n"
    python_file += f"\n{graph_script}"
    return python_file
