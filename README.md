<p align="center">
    <img src="docs/codex.png" alt="Image Description" width="300">
</p>

# Introduction


## Database Structure For Hybrid Search

> Objective: To allow programatic construction of an execution graph


This is a DAG construction problem, where the nodes are functions and the edges are parameters.

Each Node has input parameters (required and optional )and output parameters. 

Each Node is created from a NodeTemplate. This is because we can use the same Node Template multiple times within the same
execution graph. However, it it is literally the same Node then it would cause cycles. To prevent this each Node is constructed form a Node Template.

For a graph to be valid all Nodes must have sufficent edges to fill the required parameters.

ExecutionGraph
id, description, nodes, inputs, outputs, execution_type (endpoint, job, tool, action), Storage


Node needs a specific connection which maps outputs to inputs

```python
def ExecutionGraph(x,y, z) -> a, f:
    a, b, c = func(x, y, z)
    d, f = func(a, x)
    return a, f
```

```Typescript
class Node {
  edges: Edge[] = [];
  data: string;
}

class Edge {
  previousNode: Node;
  nextNode?: Node;
}
```


```sql
CREATE TABLE nodes (
  id SERIAL PRIMARY KEY,
  data VARCHAR(255)
);

CREATE TABLE edges (
  previous_node INTEGER REFERENCES nodes(id),
  next_node INTEGER REFERENCES nodes(id),
  PRIMARY KEY (previous_node, next_node)
);

```

Graph Input (A, B, C) 
    \ (A) \ (B)  \ (C)
     \     \      \
        Node       \
          \ (Z)     \
           \         \
               Node
EGNodes

EGInput
EGOutput

Node

nrequirements
ninput
noutput
