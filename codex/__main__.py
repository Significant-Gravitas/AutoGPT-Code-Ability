from sqlmodel import SQLModel, Field, Relationship, create_engine
from sqlalchemy.orm import RelationshipProperty


def create_db_and_tables():
    engine = create_engine(
        "postgresql+psycopg2://agpt_live:bnfaHGGSDF134345@0.0.0.0/agpt_product"
    )
    SQLModel.metadata.create_all(engine)


class Node(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    value: str  # Additional attributes can be added as needed

    outgoing_edges: list["Edge"] = Relationship(
        back_populates="source_node",
        sa_relationship_kwargs={
            "primaryjoin": "Node.id==Edge.source_node_id",
            "lazy": "joined",
        },
    )

    incoming_edges: list["Edge"] = Relationship(
        back_populates="target_node",
        sa_relationship_kwargs={
            "primaryjoin": "Node.id==Edge.target_node_id",
            "lazy": "joined",
        },
    )

    def __str__(self):
        return f"Node(id={self.id}, value={self.value})"


class Edge(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source_node_id: int = Field(default=None, foreign_key="node.id")
    source_node: Node = Relationship(
        back_populates="outgoing_edges",
        sa_relationship=RelationshipProperty(foreign_keys="[Edge.source_node_id]"),
    )

    target_node_id: int = Field(default=None, foreign_key="node.id")
    target_node: Node = Relationship(
        back_populates="incoming_edges",
        sa_relationship=RelationshipProperty(foreign_keys="[Edge.target_node_id]"),
    )

    def __str__(self) -> str:
        return f"Edge(id={self.id}, source_node_id={self.source_node_id}, target_node_id={self.target_node_id})"


class DAG:
    def __init__(self):
        # Initialize an empty graph
        self.graph = {}

    def add_node(self, node):
        # Add a node if it doesn't already exist
        if node not in self.graph:
            self.graph[node] = []

    def add_edge(self, start, end):
        # Add an edge, ensuring it doesn't create a cycle
        if start in self.graph and end in self.graph:
            if not self._creates_cycle(start, end):
                self.graph[start].append(end)
            else:
                raise ValueError("Adding this edge creates a cycle")
        else:
            raise ValueError("Start or end node not found")

    def _creates_cycle(self, start, end):
        # Depth-first search to detect cycles
        visited = set()
        return self._dfs(start, end, visited)

    def _dfs(self, current, target, visited):
        if current == target:
            return True
        visited.add(current)
        for neighbor in self.graph[current]:
            if neighbor not in visited:
                if self._dfs(neighbor, target, visited):
                    return True
        return False

    def __str__(self):
        output = []
        for node in self.graph:
            output.append(f"Node {node}: {self.graph[node]}")
        return "\n".join(output)


from sqlmodel import Session


def build_dag_from_nodes_and_edges(node_ids, edges):
    dag = DAG()
    import IPython
    IPython.embed()

    for node_id in node_ids:
        dag.add_node(node_id)

    for edge in edges:
        # Ensure edge is an Edge object
        if isinstance(edge, Edge):
            source_node_id = edge.source_node_id
            target_node_id = edge.target_node_id
        else:
            # Adjust this part based on the actual structure of your results
            source_node_id = edge['source_node_id']
            target_node_id = edge['target_node_id']

        if source_node_id in dag.graph and target_node_id in dag.graph:
            dag.add_edge(source_node_id, target_node_id)

    return dag



def add_node(session: Session, node: Node) -> Node:
    session.add(node)
    session.commit()
    session.refresh(node)
    return node


def add_edge(session: Session, edge: Edge) -> Edge:
    session.add(edge)
    session.commit()
    session.refresh(edge)
    return edge


from sqlalchemy import select, alias, and_
from sqlmodel import Session


from sqlalchemy import select

from sqlalchemy import select, or_

def load_dag(session: Session, start_node_id: int):
    # Fetch all nodes using recursive CTE
    recursive_query = (
        select(Node)
        .where(Node.id == start_node_id)
        .cte(name="recursive_query", recursive=True)
    )

    recursive_part = (
        select(Node)
        .join(Edge, Edge.target_node_id == Node.id)
        .join(recursive_query, Edge.source_node_id == recursive_query.c.id)
    )

    recursive_query = recursive_query.union_all(recursive_part)

    # Execute the query and get node IDs
    node_data = session.exec(select(recursive_query)).all()
    nodes = [Node(id=row[0][0], value=row[0][1]) for row in node_data]
    
    node_ids = [row[0] for row in node_data]

    # Fetch all edges where source or target node is in the obtained node IDs
    edges = session.exec(
        select(Edge).filter(
            or_(Edge.source_node_id.in_(node_ids), Edge.target_node_id.in_(node_ids))
        )
    ).all()

    return nodes, edges




# Create the database and tables
create_db_and_tables()

# Create a session and add some nodes and edges
with Session(
    create_engine(
        "postgresql+psycopg2://agpt_live:bnfaHGGSDF134345@0.0.0.0/agpt_product"
    )
) as session:
    node_a = add_node(session, Node(value="A"))
    node_b = add_node(session, Node(value="B"))
    node_c = add_node(session, Node(value="C"))

    add_edge(session, Edge(source_node_id=node_a.id, target_node_id=node_b.id))
    add_edge(session, Edge(source_node_id=node_b.id, target_node_id=node_c.id))

    # Load the DAG starting from a specific node
    node_ids, edges = load_dag(session, start_node_id=node_a.id)
    dag_object = build_dag_from_nodes_and_edges(node_ids, edges)
    print(dag_object)