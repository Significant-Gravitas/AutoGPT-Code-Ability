from examples.a_web_reader import nodes as web_nodes
from examples.b_calculator import nodes as calc_nodes
from examples.c_data_agg import nodes as data_nodes
from examples.d_blog import (
    create_post_path,
    delete_post_path,
    edit_post_path,
    login_path,
    registration_path,
)
from examples.e_inventory import (
    add_inventory_items_path,
    delete_inventory_items_path,
    track_stock_levels_path,
    update_inventory_items_path,
)
from examples.f_chat import (
    login_nodes,
    read_receipts_nodes,
    receive_message_nodes,
    registration_nodes,
    send_message_nodes,
    typing_indicator_nodes,
    user_presence_nodes,
)

nodes = [
    (web_nodes, "web_nodes"),
    (calc_nodes, "calc_nodes"),
    (data_nodes, "data_nodes"),
    (registration_path, "registration_path"),
    (login_path, "login_path"),
    (create_post_path, "create_post_path"),
    (edit_post_path, "edit_post_path"),
    (delete_post_path, "delete_post_path"),
    (add_inventory_items_path, "add_inventory_items_path"),
    (delete_inventory_items_path, "delete_inventory_items_path"),
    (update_inventory_items_path, "update_inventory_items_path"),
    (track_stock_levels_path, "track_stock_levels_path"),
    (registration_nodes, "registration_nodes"),
    (login_nodes, "login_nodes"),
    (send_message_nodes, "send_message_nodes"),
    (receive_message_nodes, "receive_message_nodes"),
    (user_presence_nodes, "user_presence_nodes"),
    (typing_indicator_nodes, "typing_indicator_nodes"),
    (read_receipts_nodes, "read_receipts_nodes"),
]

print(f"Total number of nodes: {len(nodes)}")
import re

import networkx as nx

from codex.dag import add_node, create_runner


def extract_code_blocks(output):
    # Regular expression pattern to match a code block
    code_block_regex = r"```(?:\w+)?\n([\s\S]*?)\n```"
    # Regular expression pattern to match a file name in a comment
    file_name_regex = r"Filename:\s*`([^`]+)`"
    code_blocks = []
    for match in re.finditer(code_block_regex, output):
        code_block = match.group(1)
        file_name = None
        for match in re.finditer(file_name_regex, code_block):
            file_name = match.group(1)
            break
        code_blocks.append((code_block, file_name))

    return code_blocks


# Example: reuse your existing OpenAI setup
from openai import OpenAI

# Point to the local server
client = OpenAI(base_url="http://0.0.0.0:1234/v1", api_key="not-needed")


for graph, name in nodes:
    print(f"Creating graph for {name}")
    G = nx.DiGraph()
    for node in graph:
        print(node)
        add_node(G, node.name, node)
        if "request" not in node.name and "response" not in node.name:
            print("\tGenerating Code")
            completion = client.chat.completions.create(
                model="local-model",  # this field is currently unused
                messages=[
                    {
                        "role": "system",
                        "content": "Write the python code for the "
                        "following function, also write a pytest and hypothesis tests for it. State the filename before each codeblock and add a requirements.txt codeblock",
                    },
                    {"role": "user", "content": str(node)},
                ],
                temperature=0.7,
            )

            code_blocks = extract_code_blocks(completion.choices[0].message.content)
            import os

            os.mkdir(f"nodes/{node.name}")
            with open(f"nodes/{node.name}/{node.name}.txt", "w") as ff:
                ff.write(completion.choices[0].message.content)
            for code_block, file_name in code_blocks:
                with open(f"nodes/{node.name}/{file_name}", "w") as f:
                    f.write(code_block)
            exit()
