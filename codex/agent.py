import logging
from typing import List

import networkx as nx
from sentence_transformers import SentenceTransformer
from sqlmodel import Session
from codex.chains import (
    ApplicationPaths,
    CheckComplexity,
    NodeDefinition,
    NodeGraph,
    SelectNode,
    chain_check_node_complexity,
    chain_decompose_node,
    chain_decompose_task,
    chain_generate_execution_graph,
    chain_select_from_possible_nodes,
    chain_write_node,
)
from codex.code_gen import create_fastapi_server
from codex.dag import add_node, compile_graph
from codex.database import search_for_similar_node
from codex.model import InputParameter, Node, OutputParameter, RequiredPackage


EMBEDDER = SentenceTransformer("all-mpnet-base-v2")

logger = logging.getLogger(__name__)


def parse_requirements(requirements_str: str) -> List[RequiredPackage]:
    """
    Parses a string of requirements and creates a list of RequiredPackage objects.

    Args:
    requirements_str (str): A string containing package requirements.

    Returns:
    List[RequiredPackage]: A list of RequiredPackage objects.
    """
    logger.info("🔍 Parsing requirements...")
    packages = []
    version_specifiers = ["==", ">=", "<=", ">", "<", "~=", "!="]
    if requirements_str == "":
        return packages
    for line in requirements_str.splitlines():
        if line:
            # Remove comments and whitespace
            line = line.split("#")[0].strip()
            if not line:
                continue

            package_name, version, specifier = line, None, None

            # Try to split by each version specifier
            for spec in version_specifiers:
                if spec in line:
                    parts = line.split(spec)
                    package_name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else None
                    specifier = spec
                    break

            package = RequiredPackage(
                package_name=package_name, version=version, specifier=specifier
            )
            packages.append(package)

    return packages


def process_node(
    session: Session,
    node: NodeDefinition,
    processed_nodes: List[Node],
    ap: ApplicationPaths,
    dag: nx.DiGraph,
    embedder: SentenceTransformer,
    engine,
):
    """
    Processes a single node in the DAG.

    Args:
    session (Session): Database session.
    node (NodeDefinition): The current node to process.
    ap (ApplicationPaths): Application paths context.
    dag (nx.DiGraph): The directed acyclic graph of nodes.
    embedder (SentenceTransformer): The sentence transformer for embedding.
    """
    logger.info(f"🚀 Processing node: {node.name}")

    if "request" in node.name.lower() or "response" in node.name.lower():
        logger.info(f"🔗 Adding request/response node: {node.name}")
        input_params = (
            [InputParameter(**p.dict()) for p in node.input_params]
            if node.input_params
            else []
        )
        output_params = (
            [OutputParameter(**p.dict()) for p in node.output_params]
            if node.output_params
            else []
        )
        req_resp_node = Node(
            name=node.name,
            description=node.description,
            input_params=input_params,
            output_params=output_params,
        )
        add_node(dag, node.name, req_resp_node)
        return req_resp_node
    else:
        logger.info(f"🔍 Searching for similar nodes for: {node.name}")
        possible_nodes = search_for_similar_node(session, node, embedder)
        logger.debug(f"Possible nodes: {possible_nodes}")

        if not possible_nodes:
            logger.warning(f"No similar nodes found for: {node.name}")
            selected_node = SelectNode(node_id="new")
            logger.debug(f"Selected node: {selected_node}")
        else:
            nodes_str = ""
            for i, n in enumerate(possible_nodes):
                nodes_str += f"Node ID: {i}\n{n}\n"

            logger.info(
                f"✅ Found similar nodes, selecting the appropriate one for: {node.name}"
            )
            available_outputs = []
            for n in processed_nodes:
                available_outputs.extend(n.output_params)

            output_params = node.output_params

            selected_node = SelectNode.parse_obj(
                chain_select_from_possible_nodes.invoke(
                    {
                        "nodes": nodes_str,
                        "requirement": node,
                        "avaliable_params": available_outputs,
                        "required_output_params": output_params,
                    }
                )
            )
            logger.debug(f"Selected node: {selected_node}")
        if selected_node.node_id == "new":
            logger.info(f"🆕 Processing new node: {node.name}")
            complexity = CheckComplexity.parse_obj(
                chain_check_node_complexity.invoke({"node": node})
            )
            logger.debug(f"Node complexity: {complexity}")

            if not complexity.is_complex:
                logger.info(f"📝 Writing new node code for: {node.name}")
                requirements, code = chain_write_node.invoke({"node": node})
                required_packages = parse_requirements(requirements)

                logger.info(f"📦 Adding new node to the database: {node.name}")

                input_params = [InputParameter(**p.dict()) for p in node.input_params]
                output_params = [
                    OutputParameter(**p.dict()) for p in node.output_params
                ]
                new_node = Node(
                    name=node.name,
                    description=node.description,
                    input_params=input_params,
                    output_params=output_params,
                    required_packages=required_packages,
                    code=code,
                )
                new_node.embedding = embedder.encode(
                    node.description,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                )
                session.add(new_node)
                session.commit()
                logger.info(f"✅ New node added: {node.name}")
                logger.info(f"🔗 Adding new node to the DAG: {node.name}")
                add_node(dag, new_node.name, new_node)
                return new_node
            else:
                logger.warning(f"🔄 Node is complex, decomposing: {node.name}")
                sub_graph = NodeGraph.parse_obj(
                    chain_decompose_node.invoke(
                        {
                            "application_context": ap.application_context,
                            "node": node,
                        }
                    )
                )
                for sub_node in sub_graph.nodes:
                    process_node(
                        session, sub_node, processed_nodes, ap, dag, EMBEDDER, engine
                    )
        else:
            node_id = int(selected_node.node_id)
            assert node_id < len(possible_nodes), "Invalid node id"
            node: Node = possible_nodes[node_id]

            # Map I/O params
            if selected_node.input_map:
                logger.info(f"🔗 Mapping input params for: {node.name}")
                for param in node.input_params:
                    if param.name in selected_node.input_map:
                        logger.warning(
                            f"Mapping input param: {param.name} to {selected_node.input_map[param.name]}"
                        )
                        param.name = selected_node.input_map[param.name]

            if selected_node.output_map:
                logger.info(f"🔗 Mapping output params for: {node.name}")
                for param in node.output_params:
                    if param.name in selected_node.output_map:
                        logger.warning(
                            f"Mapping input param: {param.name} to {selected_node.output_map[param.name]}"
                        )
                        param.name = selected_node.output_map[param.name]

            logger.info(f"🔗 Adding existing node to the DAG: {node.name}")
            add_node(dag, node.name, node)
            return node


def run(task_description: str, engine):
    """
    Runs the task processing pipeline.

    Args:
    task_description (str): Description of the task to run.

    Returns:
    The generated code for the task.
    """
    logger.info(f"🏁 Running task: {task_description}")

    # Decompose task into application paths
    ap = ApplicationPaths.parse_obj(
        chain_decompose_task.invoke({"task": task_description})
    )
    logger.info("✅ Task decomposed into application paths")
    logger.debug(f"Application paths: {ap}")
    generated_data = []
    with Session(engine) as session:
        for path_index, path in enumerate(ap.execution_paths, start=1):
            logger.info(
                f"🔄 Processing path {path_index}/{len(ap.execution_paths)} - {path.name}: {path.description}"
            )

            dag = nx.DiGraph()
            logger.info("📈 Generating execution graph")

            ng = NodeGraph.parse_obj(
                chain_generate_execution_graph.invoke(
                    {
                        "application_context": ap.application_context,
                        "api_route": path,
                        "graph_name": path.name,
                    }
                )
            )
            logger.info("🌐 Execution graph generated")
            logger.debug(f"Execution graph: {ng}")
            processed_nodes = []
            for node_index, node in enumerate(ng.nodes, start=1):
                logger.info(
                    f"🔨 Processing node {node_index}/{len(ng.nodes)}: {node.name}"
                )
                processed_node = process_node(
                    session, node, processed_nodes, ap, dag, EMBEDDER, engine
                )
                processed_nodes.append(processed_node)

            logger.info("🔗 All nodes processed, creating runner")
            data = compile_graph(dag, path)
            generated_data.append(data)
            logger.info("🏃 Runner created successfully")

    logger.info("🎉 Task processing completed")
    return create_fastapi_server(generated_data)


if __name__ == "__main__":
    from colorama import Fore, Style, init

    init()

    class CustomFormatter(logging.Formatter):
        """Logging Formatter to add colors and count warning / errors"""

        FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        FORMATS = {
            logging.DEBUG: Fore.CYAN + FORMAT + Style.RESET_ALL,
            logging.INFO: Fore.GREEN + FORMAT + Style.RESET_ALL,
            logging.WARNING: Fore.YELLOW + FORMAT + Style.RESET_ALL,
            logging.ERROR: Fore.RED + FORMAT + Style.RESET_ALL,
            logging.CRITICAL: Fore.RED + FORMAT + Style.RESET_ALL,
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    ch.setFormatter(CustomFormatter())

    # Add the handlers to the logger
    logger.addHandler(ch)

    code = run(
        "Develop a small script that takes a URL as input and returns the webpage in Markdown format. Focus on converting basic HTML tags like headings, paragraphs, and lists."
    )
