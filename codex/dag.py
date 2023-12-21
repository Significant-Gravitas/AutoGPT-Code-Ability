from typing import Dict, Tuple

import networkx as nx

from .model import Node


def add_node(graph: nx.DiGraph, node_name: str, node: Node):
    if graph.number_of_nodes() == 0:
        graph.add_node(node_name, node=node)
        return
    # Check if node's input parameters are satisfied by the existing nodes in the graph
    if node.input_params:
        input_params_needed = {(p.name, p.prama_type): p for p in node.input_params}
    else:
        input_params_needed = {}

    # Find nodes in the graph that can provide the required input parameters
    providers: Dict[Tuple[str, str], Node] = {}
    for n in graph.nodes:
        existing_node: Node = graph.nodes[n]["node"]
        assert isinstance(existing_node, Node)
        if existing_node.output_params:
            for output_param in existing_node.output_params:
                param_key = (output_param.name, output_param.prama_type)
                if param_key in input_params_needed:
                    providers[param_key] = n

    # Check if all input parameters are available
    if len(input_params_needed) != len(providers):
        raise ValueError(
            "Not all input parameters can be satisfied by the current graph."
        )

    # Add the new node
    graph.add_node(node_name, node=node)

    # Connect the new node to its parameter providers
    for param_key, provider_node in providers.items():
        graph.add_edge(provider_node, node_name, connection_type=param_key[0])


def create_runner(graph: nx.DiGraph):
    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise nx.NetworkXError("Graph is not a Directed Acyclic Graph (DAG)")

    output_name_map: Dict[str, str] = {}

    script = ""
    for node_name in nx.topological_sort(graph):
        node: Node = graph.nodes[node_name]["node"]
        if "request" in node_name:
            script += node.request_to_code()
        elif "response" in node_name:
            script += node.response_to_code(output_name_map)
        else:
            code, unique_output_names_map = node.to_code(output_name_map)
            output_name_map: Dict[str, str] = {
                **output_name_map,
                **unique_output_names_map,
            }
            script += f"{code}\n"
    return script
