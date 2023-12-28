from typing import List, Tuple

from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, select

from .model import InputParameter, Node, OutputParameter


def search_nodes_by_params(
    session: Session,
    query: List[float],
    input_param_types: List[str],
    output_param_types: List[str],
    similarity_threshold: float = 0.5,
    limit: int = 5,
) -> List[Tuple[Node, float]]:
    """
    Search for nodes based on input and output parameter types,
    ordering by similarity to the query embedding.

    :param session: The database session.
    :param query: The query embedding for cosine distance calculation.
    :param input_param_types: A list of required input parameter types.
    :param output_param_types: A list of required output parameter types.
    :param similarity_threshold: The threshold for cosine similarity lower
                                 is better (default 0.5).
    :param limit: The number of results to limit to (default 5).
    :return: A list of tuples, each containing a Node object and
             its corresponding cosine distance.
    """
    # Base query for Node, including cosine distance
    query = select(  # type: ignore
        Node,
        Node.embedding.cosine_distance(query_embedding).label(  # type: ignore
            "cosine_distance"
        ),  # type: ignore
    ).where(
        Node.embedding.cosine_distance(query) <= similarity_threshold  # type: ignore
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
            query = query.where(  # type: ignore
                subquery == input_param_types.count(param_type)
            )

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
            query = query.where(  # type: ignore
                subquery == output_param_types.count(param_type)
            )

    # Add ordering and limit
    query = query.order_by(  # type: ignore
        Node.embedding.cosine_distance(query_embedding)  # type: ignore
    ).limit(limit)

    # Execute the query and fetch results
    return session.exec(query).fetchall()  # type: ignore


if __name__ == "__main__":
    import os

    from sentence_transformers import SentenceTransformer  # type: ignore

    from examples.a_web_reader import nodes as web_reader_nodes

    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./codex.db")
    engine = create_engine(DATABASE_URL)

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for node in web_reader_nodes:
            # Add the node to the session
            session.add(node)
            session.commit()
            session.refresh(node)

    embedder = SentenceTransformer("all-mpnet-base-v2")
    query_embedding: List[float] = embedder.encode(  # type: ignore
        "Download page", normalize_embeddings=True, convert_to_numpy=True
    )

    cosine_similarity_threshold = 0.5

    with Session(engine) as session:
        input_types = ["str"]
        output_types = ["str"]
        ans = search_nodes_by_params(
            session, query_embedding, input_types, output_types
        )
        import IPython

        IPython.embed()  # type: ignore
