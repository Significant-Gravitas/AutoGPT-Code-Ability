import logging
from typing import List

import networkx as nx
from sentence_transformers import SentenceTransformer
from sqlmodel import Session

from codex.chains.write_node import write_code_chain
from codex.code_gen import create_fastapi_server
from codex.dag import add_node, compile_graph
from codex.database import search_for_similar_node
from codex.model import InputParameter, Node, OutputParameter
from codex.chains.decompose_task import chain_decompose_task, ApplicationPaths
from codex.chains.generate_graph import chain_generate_execution_graph, NodeDefinition, NodeGraph, chain_decompose_node
from codex.chains.select_node import chain_select_from_possible_nodes, SelectNode
from codex.chains.check_node_complexity import CheckComplexity

EMBEDDER = SentenceTransformer("all-mpnet-base-v2")

logger = logging.getLogger(__name__)


def select_node_from_possible_nodes(
    possible_nodes, processed_nodes, node
) -> SelectNode:
    if not possible_nodes:
        logger.warning(f"No similar nodes found for: {node.name}")
        return SelectNode(node_id="new")
    
    correct_possible_nodes = []
    for n in possible_nodes:
        if len(n.input_params) == len(node.input_params) and len(n.output_params) <= len(node.output_params):
            correct_possible_nodes.append(n)

    # Create the node list for the prompt
    nodes_str = ""
    for i, n in enumerate(possible_nodes):
        nodes_str += f"Node ID: {i}\n{n}\n"

    avaliable_inpurt_params = []
    for n in processed_nodes:
        if n and n.output_params:
            avaliable_inpurt_params.extend(n.output_params)

    return chain_select_from_possible_nodes(
        nodes_str=nodes_str,
        requested_node=node,
        avaliable_inpurt_params=avaliable_inpurt_params,
        possible_nodes=correct_possible_nodes,
    )



def process_request_response_node(
    node: NodeDefinition,
    dag: nx.DiGraph,
):
    logger.debug(f"🔗 Adding request/response node: {node.name}")
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
    logger.debug(f"🚀 Processing node: {node.name}")

    if "request" in node.name.lower() or "response" in node.name.lower():
        return process_request_response_node(node, dag)
    else:
        logger.debug(f"🔍 Searching for similar nodes for: {node.name}")
        possible_nodes = search_for_similar_node(session, node, embedder)

        selected_node = select_node_from_possible_nodes(
            possible_nodes, processed_nodes, node
        )

        if selected_node.node_id == "new":
            logger.debug(f"🆕 Processing new node: {node.name}")
            # complexity = CheckComplexity.parse_obj(
            #     chain_check_noxde_complexity.invoke({"node": node})
            # )
            complexity = CheckComplexity(is_complex=False)
            logger.debug(f"Node complexity: {complexity}")

            if not complexity.is_complex:
                logger.debug(f"📝 Writing new node code for: {node.name}")
                required_packages, code = write_code_chain(invoke_params={"node": node})

                logger.debug(f"📦 Adding new node to the database: {node.name}")

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
                logger.debug(f"✅ New node added: {node.name}")
                logger.debug(f"🔗 Adding new node to the DAG: {node.name}")
                add_node(dag, new_node.name, new_node)
                return new_node
            else:
                logger.warning(f"🔄 Node is complex, decomposing: {node.name}")
                sub_graph_nodes = chain_decompose_node(
                            application_context= ap.application_context,
                            node=node,
                        )
                # TODO: vaidate sub_graph_nodes
                for sub_node in sub_graph_nodes.nodes:
                    if not (
                        "request" in sub_node.name.lower()
                        or "response" in sub_node.name.lower()
                    ):
                        pnode = process_node(
                            session,
                            sub_node,
                            processed_nodes,
                            ap,
                            dag,
                            EMBEDDER,
                            engine,
                        )
                        # TODO This maybe causing a bug where the node is not added to the
                        # processed nodes list as processed nodes is not returning a node
                        if pnode:
                            processed_nodes.append(pnode)

        else:
            node_id = int(selected_node.node_id)
            assert node_id < len(possible_nodes), "Invalid node id"
            node: Node = possible_nodes[node_id]
            logger.debug(f"✅ Node selected: {node}")
            # Map I/O params
            if selected_node.input_map:
                logger.debug(f"🔗 Mapping input params for: {node.name}")
                for param in node.input_params:
                    if param.name in selected_node.input_map:
                        logger.warning(
                            f"Mapping input param: {param.name} to {selected_node.input_map[param.name]}"
                        )
                        param.name = selected_node.input_map[param.name]

            if selected_node.output_map:
                logger.debug(f"🔗 Mapping output params for: {node.name}")
                for param in node.output_params:
                    if param.name in selected_node.output_map:
                        logger.warning(
                            f"Mapping input param: {param.name} to {selected_node.output_map[param.name]}"
                        )
                        param.name = selected_node.output_map[param.name]

            logger.debug(f"🔗 Adding existing node to the DAG: {node.name}")
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
    try:
        logger.info(f"🏁 Running task: {task_description}")

        # Decompose task into application paths
        ap = chain_decompose_task(task_description)
        
        logger.debug("✅ Task decomposed into application paths")
        logger.debug(f"Application paths: {ap}")
        generated_data = []
        with Session(engine) as session:
            for path_index, path in enumerate(ap.execution_paths, start=1):
                try:
                    logger.info(
                        f"🔄 Processing path {path_index}/{len(ap.execution_paths)} - {path.name}: {path.description}"
                    )

                    dag = nx.DiGraph()
                    logger.debug("📈 Generating execution graph")

                    ng = chain_generate_execution_graph(ap.application_context, path, path.name)

                    logger.debug("🌐 Execution graph generated")
                    logger.debug(f"Execution graph: {ng}")
                    processed_nodes = []
                    for node_index, node in enumerate(ng.nodes, start=1):
                        logger.info(
                            f"🔨 Processing node {node_index}/{len(ng.nodes)}: {node.name}"
                        )
                        processed_node = process_node(
                            session, node, processed_nodes, ap, dag, EMBEDDER, engine
                        )
                        if process_node:
                            processed_nodes.append(processed_node)

                    logger.info("🔗 All nodes processed, compiling graph")
                    data = compile_graph(dag, path)
                    generated_data.append(data)
                except Exception as e:
                    logger.error(f"❌ Path processing failed: {e}\n\nDetails:\n{ng}")
                    raise e

        runner = create_fastapi_server(generated_data)
        logger.info("🎉 Task processing completed")
        return runner
    except Exception as e:
        logger.error(f"❌ Task processing failed: {e}\n\nDetails:\n{ap}")
        raise e


if __name__ == "__main__":
    from colorama import Fore, Style, init
    from sqlalchemy import create_engine

    init()
    DATABASE_URL = "postgresql://agpt_live:bnfaHGGSDF134345@0.0.0.0:5432/agpt_product"
    engine = create_engine(DATABASE_URL)

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
        "Create a system to manage inventory for a small business. Features should include adding, updating, and deleting inventory items, as well as tracking stock levels.",
        engine,
    )
