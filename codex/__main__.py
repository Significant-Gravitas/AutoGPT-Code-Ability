import networkx as nx

from .model import Node, Parameter

# Create a directed graph
G = nx.DiGraph()


request_node = Node(
    description="Takes in the url of a website",
    name="request_node",
    input_params=None,
    output_params=[
        Parameter(prama_type="str", name="url", description="The url of the website"),
        Parameter(
            prama_type="str",
            name="format",
            description="the format to convert the webpage too",
        ),
    ],
    package_requirements=[],  # Add the missing argument for "package_requirements"
)

verify_url = Node(
    description="Verifies that the url is valid",
    name="verify_url",
    input_params=[
        Parameter(prama_type="str", name="url", description="The url of the website")
    ],
    output_params=[
        Parameter(
            prama_type="str",
            name="valid_url",
            description="The url of the website if it is valid",
        )
    ],
    package_requirements=[],
)

download_page = Node(
    description="Downloads the webpage",
    name="download_page",
    input_params=[
        Parameter(
            prama_type="str",
            name="valid_url",
            description="The url of the website if it is valid",
        )
    ],
    output_params=[
        Parameter(
            prama_type="str",
            name="html",
            description="The html of the webpage",
        )
    ],
    package_requirements=[],
)

convert_page = Node(
    description="Converts the webpage to the desired format",
    name="convert_page",
    input_params=[
        Parameter(
            prama_type="str",
            name="html",
            description="The html of the webpage",
        ),
        Parameter(
            prama_type="str",
            name="format",
            description="the format to convert the webpage too",
        ),
    ],
    output_params=[
        Parameter(
            prama_type="str",
            name="converted_page",
            description="The converted webpage",
        )
    ],
    package_requirements=[],
)

response_node = Node(
    name="response_node",
    description="Returns the converted webpage",
    input_params=[
        Parameter(
            prama_type="str",
            name="converted_page",
            description="The converted webpage",
        )
    ],
    output_params=[],
    package_requirements=[],
)

G.add_node("request_node", node=request_node)

print(request_node)
print("\n")
print(convert_page)
print("\n")


def add_node(graph, node_name, node):
    # Check if node's input parameters are satisfied by the existing nodes in the graph
    if node.input_pramas:
        input_params_needed = {(p.name, p.prama_type): p for p in node.input_pramas}
    else:
        input_params_needed = {}

    # Find nodes in the graph that can provide the required input parameters
    providers = {}
    for n in graph.nodes:
        existing_node = graph.nodes[n]["node"]
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


# Example usage
add_node(G, "verify_url", verify_url)
add_node(G, "download_page", download_page)
add_node(G, "convert_page", convert_page)
add_node(G, "response_node", response_node)

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# Assuming G is your graph


# Helper function to determine layers
def assign_layers(G, start_node):
    layers = {}
    layer = 0
    queue = [(start_node, layer)]
    while queue:
        node, layer = queue.pop(0)
        if node not in layers:
            layers[node] = layer
            queue.extend([(adj, layer + 1) for adj in G.successors(node)])
    return layers


# Assign layers starting from 'request_node'
layers = assign_layers(G, "request_node")

# Determine the maximum number of nodes in any layer
layer_counts = {layer: 0 for layer in set(layers.values())}
for layer in layers.values():
    layer_counts[layer] += 1
max_width = max(layer_counts.values())

# Calculate positions
pos = {}
layer_positions = {layer: 0 for layer in set(layers.values())}
for node, layer in layers.items():
    width_nodes = layer_counts[layer]
    x_spacing = max_width / (width_nodes + 1)
    x_positions = np.linspace(x_spacing, max_width - x_spacing, width_nodes)
    pos[node] = (x_positions[layer_positions[layer]], -layer)
    layer_positions[layer] += 1

# Draw the graph
nx.draw(
    G,
    pos,
    with_labels=True,
    node_color="skyblue",
    edge_color="gray",
    node_size=3000,
    font_size=10,
)

# Node labels

# Edge labels
edge_labels = {(u, v): G[u][v]["connection_type"] for u, v in G.edges()}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

# Show the plot
plt.show()


plt.savefig("plot.png")

import networkx as nx

# Assuming G is your graph

print(f"Execution order: {list(nx.topological_sort(G))}")


def create_runner(graph: nx.DiGraph):
    # Check if the graph is a DAG
    if not nx.is_directed_acyclic_graph(G):
        raise nx.NetworkXError("Graph is not a Directed Acyclic Graph (DAG)")

    output_name_map: Dict[str, str] = {}

    script = ""
    for node_name in nx.topological_sort(G):
        node: Node = G.nodes[node_name]["node"]
        if node_name == "request_node":
            script += node.request_to_code()
        elif node_name == "response_node":
            script += node.response_to_code(output_name_map)
        else:
            code, unique_output_names_map = node.to_code(output_name_map)
            output_name_map: Dict[str, str] = {
                **output_name_map,
                **unique_output_names_map,
            }
            script += f"{code}\n"
    return script


print("\n```\n")
print(create_runner(G))
print("```")
