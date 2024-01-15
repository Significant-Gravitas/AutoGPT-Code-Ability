import logging
from collections import defaultdict
from typing import Dict, List, Tuple

import black
import isort
import networkx as nx

from codex.chains.decompose_task import ExecutionPath

from .code_gen import NodeDef, convert_graph_to_code
from .model import FunctionData, Node, RequiredPackage

logger = logging.getLogger(__name__)


def add_node(graph: nx.DiGraph, node_name: str, node: Node, node_def) -> bool:
    if graph.number_of_nodes() == 0:
        graph.add_node(node_name, node=node)
        return True

    if "response" not in node_name and not node.output_params:
        logger.error(f"Node {node_name} has no output parameters\n {node}")

    # Check if node's input parameters are satisfied by the existing nodes in the graph
    if node.input_params:
        input_params_needed = [f"{p.name}: {p.param_type}" for p in node.input_params]
    else:
        input_params_needed = {}

    # Find nodes in the graph that can provide the required input parameters
    # TODO: This method requires an exact match of the variable name and type
    providers: Dict[Tuple[str, str], Node] = {}
    for n in graph.nodes:
        existing_node: Node = graph.nodes[n]["node"]

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
    graph.add_node(node_name, node=node, node_deg=node_def)

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
    try:
        # First, sort the imports using isort
        sorted_content = isort.code(file_content)

        # Then, format the code using black
        formatted_content = black.format_str(sorted_content, mode=black.FileMode())
    except Exception as e:
        logger.error(f"Error formatting code: {e}")
        logger.error(f"Code:\n {file_content}")
    return formatted_content


def generate_requirements_txt(packages: List[RequiredPackage]) -> str:
    resolved_packages = defaultdict(list)

    # Aggregate versions and specifiers for each package
    for package in packages:
        resolved_packages[package.package_name].append(
            (package.version, package.specifier)
        )

    requirements = []
    for package, versions_specifiers in resolved_packages.items():
        # Handle different cases of version and specifier here
        # For simplicity, we just pick the first version and specifier encountered
        # More complex logic might be needed depending on the requirement
        version, specifier = versions_specifiers[0]
        if version and specifier:
            requirement = f"{package}{specifier}{version}"
        elif version:
            requirement = f"{package}=={version}"
        else:
            requirement = package
        requirements.append(requirement)

    return "\n".join(requirements)


def compile_graph(
    graph: List[NodeDef], node_implementations: List[Node], ep: ExecutionPath
):
    # Check if the graph is a DAG
    python_file = ""
    requirements = []
    function_name = (
        ep.name.strip().replace(" ", "_").replace("-", "_").replace("/", "").lower()
        + "_request"
    )

    graph_script = convert_graph_to_code(graph, function_name)

    for node in node_implementations:
        python_file += f"\n\n{node.code}"
        requirements.extend(node.required_packages)

    python_file += f"\n\n{graph_script}"
    requirements_txt = generate_requirements_txt(requirements)

    return FunctionData(
        function_name=function_name,
        code=format_and_sort_code(python_file),
        requirements_txt=requirements_txt,
        endpoint_name=ep.endpoint_name,
    )
