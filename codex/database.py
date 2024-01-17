from typing import List, Optional

from openai import OpenAI
from sqlalchemy import func
from sqlmodel import Session, select

from .model import InputParameter, Node, OutputParameter


def select_node_by_id(session: Session, node_id: int) -> Optional[Node]:
    """
    Selects a single node by its ID.

    Parameters:
    session (Session): The database session.
    node_id (int): The ID of the node to retrieve.

    Returns:
    Optional[Node]: The node if found, otherwise None.
    """
    statement = select(Node).where(Node.id == node_id)
    results = session.exec(statement)
    node = results.first()
    return node


def search_for_similar_node(session: Session, node: Node) -> Optional[List[Node]]:
    input_param_types = None
    output_param_types = None
    if node.input_params:
        input_param_types = [param.param_type for param in node.input_params]
    if node.output_params:
        output_param_types = [param.param_type for param in node.output_params]

    client = OpenAI()

    oai_response = client.embeddings.create(
        model="text-embedding-ada-002", input=node.description, encoding_format="float"
    )
    query = oai_response.data[0].embedding
    return search_nodes_by_params(
        session=session,
        description=query,
        input_param_types=input_param_types,
        output_param_types=output_param_types,
        similarity_threshold=0.3,
    )


def search_nodes_by_params(
    session: Session,
    description: List[float],
    input_param_types: Optional[List[str]] = None,
    output_param_types: Optional[List[str]] = None,
    similarity_threshold: float = 0.5,
    limit: int = 5,
) -> Optional[List[Node]]:
    """
    Search for nodes based on input and output parameter types,
    ordering by similarity to the query embedding.

    :param session: The database session.
    :param description: The query embedding for cosine distance calculation.
    :param input_param_types: A list of required input parameter types.
    :param output_param_types: A list of required output parameter types.
    :param similarity_threshold: The threshold for cosine similarity lower
                                 is better (default 0.5).
    :param limit: The number of results to limit to (default 5).
    :return: A list of Node objects.
    """
    try:
        # Check if the Node table is empty
        if session.query(Node).first() is None:
            return None  # Return an empty list if no nodes are present

        # Base query for Node, including cosine distance
        query = select(Node).where(
            Node.embedding.cosine_distance(description) <= similarity_threshold
        )

        # Adding conditions for input parameters
        if input_param_types:
            for param_type in set(input_param_types):
                subquery = (
                    select(func.count(InputParameter.id))
                    .where(
                        InputParameter.node_id == Node.id,
                        InputParameter.param_type == param_type,
                    )
                    .as_scalar()
                )
                query = query.where(subquery == input_param_types.count(param_type))

        # Adding conditions for output parameters
        if output_param_types:
            for param_type in set(output_param_types):
                subquery = (
                    select(func.count(OutputParameter.id))
                    .where(
                        OutputParameter.node_id == Node.id,
                        OutputParameter.param_type == param_type,
                    )
                    .as_scalar()
                )
                query = query.where(subquery == output_param_types.count(param_type))

        # Add ordering and limit
        query = query.order_by(Node.embedding.cosine_distance(description)).limit(limit)

        # Execute the query and fetch results
        return session.exec(query).fetchall()
    except Exception as e:
        # Log the exception and return an empty list or handle as appropriate
        print(f"An error occurred: {e}")
        return None
