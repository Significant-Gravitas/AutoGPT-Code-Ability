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

nodes = (
    web_nodes
    + calc_nodes
    + data_nodes
    + registration_path
    + login_path
    + create_post_path
    + edit_post_path
    + delete_post_path
    + add_inventory_items_path
    + delete_inventory_items_path
    + update_inventory_items_path
    + track_stock_levels_path
    + registration_nodes
    + login_nodes
    + send_message_nodes
    + receive_message_nodes
    + user_presence_nodes
    + typing_indicator_nodes
    + read_receipts_nodes
)

print(f"Total number of nodes: {len(nodes)}")
