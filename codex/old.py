from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, SQLModel, create_engine


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
        },
    )

    incoming_edges: list["Edge"] = Relationship(
        back_populates="target_node",
        sa_relationship_kwargs={
            "primaryjoin": "Node.id==Edge.target_node_id",
        },
    )


class Edge(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    source_node_id: int = Field(default=None, foreign_key="node.id")
    source_node: Node = Relationship(
        back_populates="outgoing_edges",
        sa_relationship=RelationshipProperty(
            foreign_keys="[Edge.source_node_id]"
        ),
    )

    target_node_id: int = Field(default=None, foreign_key="node.id")
    target_node: Node = Relationship(
        back_populates="incoming_edges",
        sa_relationship=RelationshipProperty(
            foreign_keys="[Edge.target_node_id]"
        ),
    )

    def __str__(self) -> str:
        return f"Edge(id={self.id}, source_node_id={self.source_node_id}, target_node_id={self.target_node_id})"


class DAG:
    def __init__(self):
        # Initialize an empty graph
        self.graph = {}

    def add_node(self, node):
        # Add a node if it doesn't already exist
        if node.id not in self.graph:
            self.graph[node.id] = node

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


def build_dag_from_nodes_and_edges(nodes, edges):
    dag = DAG()

    for node in nodes:
        dag.add_node(node)

    for edge in edges:
        edge = edge[0]
        print(edge)
        # Ensure edge is an Edge object
        if isinstance(edge, Edge):
            dag.add_edge(edge.source_node_id, edge.target_node_id)

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


from sqlalchemy import alias, and_, or_, select
from sqlalchemy.orm import selectinload
from sqlmodel import Session


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

    # Execute the node query and get node IDs and values
    node_data = session.exec(select(recursive_query)).all()
    node_ids = [row[0] for row in node_data]

    # Fetch nodes again, this time with edges
    nodes = session.exec(
        select(Node)
        .options(
            selectinload(Node.outgoing_edges),
            selectinload(Node.incoming_edges),
        )
        .where(Node.id.in_(node_ids))
    ).all()

    nodes = [node[0] for node in nodes]

    return nodes


# Create the database and tables
create_db_and_tables()

# Create a session and add some nodes and edges
with Session(
    create_engine(
        "postgresql+psycopg2://agpt_live:bnfaHGGSDF134345@0.0.0.0/agpt_product"
    )
) as session:
    A = Node(id=1111, value="A")
    B = Node(id=2222, value="B")
    C = Node(id=3333, value="C")
    D = Node(id=4444, value="D")

    AB = Edge(id=1122, source_node_id=A.id, target_node_id=B.id)
    BC = Edge(id=2233, source_node_id=B.id, target_node_id=C.id)
    CD = Edge(id=3344, source_node_id=C.id, target_node_id=D.id)
    AC = Edge(id=1133, source_node_id=A.id, target_node_id=C.id)

    A.outgoing_edges.append(AB)
    A.outgoing_edges.append(AC)
    B.outgoing_edges.append(BC)
    C.outgoing_edges.append(CD)

    B.incoming_edges.append(AB)
    C.incoming_edges.append(BC)
    D.incoming_edges.append(CD)

    import IPython

    IPython.embed()

    for node in [A, B, C, D]:
        n = add_node(session, node)
        print(n)

    for edge in [AB, BC, CD, AC]:
        add_edge(session, edge)
    # Load the DAG starting from a specific node
    node_ids, edges = load_dag(session, start_node_id=A.id)
    import IPython

    IPython.embed()

    dag_object = build_dag_from_nodes_and_edges(node_ids, edges)

    print(dag_object)
