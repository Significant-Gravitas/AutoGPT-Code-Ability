import logging
from typing import Dict, Tuple

import black
import isort
import networkx as nx

from .chains import ExecutionPath
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


def refactor_imports(file_content: str) -> str:
    from_imports = {}
    import_lines = set()
    other_lines = []

    for line in file_content.split("\n"):
        # Check if the line is a 'from' import.
        if line.startswith("from "):
            module, imported = line.split(" import ")
            if module in from_imports:
                from_imports[module].add(imported)
            else:
                from_imports[module] = {imported}
        elif line.startswith("import "):
            import_lines.add(line)
        else:
            other_lines.append(line)

    # Consolidate 'from' imports.
    consolidated_from_imports = [
        f"{module} import {', '.join(sorted(items))}"
        for module, items in from_imports.items()
    ]

    # Sort all import statements.
    all_imports = sorted(list(import_lines) + consolidated_from_imports)

    # Combine imports with the rest of the file.
    sorted_imports = "\n".join(all_imports)
    rest_of_file = "\n".join(other_lines)
    refactored_file = f"{sorted_imports}\n\n{rest_of_file}"

    return refactored_file


def format_and_sort_code(file_content: str) -> str:
    # First, sort the imports using isort
    sorted_content = isort.code(file_content)

    # Then, format the code using black
    formatted_content = black.format_str(sorted_content, mode=black.FileMode())

    return formatted_content


def compile_graph(graph: nx.DiGraph, ep: ExecutionPath):
    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(graph):
        raise nx.NetworkXError("Graph is not a Directed Acyclic Graph (DAG)")
    output_name_map: Dict[str, str] = {}
    python_file = ""
    graph_script = ""
    for node_name in nx.topological_sort(graph):
        node: Node = graph.nodes[node_name]["node"]
        if "request" in node_name:
            node.name = (
                ep.name.replace(" ", "_")
                .replace("-", "_")
                .replace("/", "")
                .strip()
            )
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
    return format_and_sort_code(refactor_imports(python_file))
