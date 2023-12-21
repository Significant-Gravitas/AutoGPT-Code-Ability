import networkx as nx
from .model import Node
from typing import Dict, Tuple


def add_node(graph: nx.DiGraph, node_name: str, node: Node):
    # Check if node's input parameters are satisfied by the existing nodes in the graph
    if node.input_pramas:
        input_params_needed = {(p.name, p.prama_type): p for p in node.input_pramas}
    else:
        input_params_needed = {}

    # Find nodes in the graph that can provide the required input parameters
    providers: Dict[Tuple[str, str], Node] = {}
    for n in graph.nodes:
        existing_node: Node = graph.nodes[n]["node"]
        assert isinstance(existing_node, Node)
        if existing_node.output_pramas:
            for output_param in existing_node.output_pramas:
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
