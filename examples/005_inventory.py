from codex.model import Node, Parameter

# Execution Path 1: Adding Inventory Items

execution_path_1 = [
    Node(
        description="Takes in details of a new inventory item",
        name="request_node_add",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="str",
                name="item_name",
                description="Name of the inventory item",
            ),
            Parameter(
                prama_type="int", name="quantity", description="Quantity of the item"
            ),
            Parameter(
                prama_type="float", name="price", description="Price of the item"
            ),
        ],
        package_requirements=[],
    ),
    Node(
        description="Adds a new item to the inventory",
        name="add_inventory_item",
        input_params=[
            Parameter(
                prama_type="str",
                name="item_name",
                description="Name of the inventory item",
            ),
            Parameter(
                prama_type="int", name="quantity", description="Quantity of the item"
            ),
            Parameter(
                prama_type="float", name="price", description="Price of the item"
            ),
        ],
        output_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item addition",
            )
        ],
        package_requirements=[],
    ),
    Node(
        name="response_node_add",
        description="Returns confirmation of item addition",
        input_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item addition",
            )
        ],
        output_params=[],
        package_requirements=[],
    ),
]

# Execution Path 2: Updating Inventory Items

execution_path_2 = [
    Node(
        description="Takes in details for updating an inventory item",
        name="request_node_update",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="str", name="item_id", description="ID of the inventory item"
            ),
            Parameter(
                prama_type="int",
                name="quantity",
                description="New quantity of the item",
                optional=True,
            ),
            Parameter(
                prama_type="float",
                name="price",
                description="New price of the item",
                optional=True,
            ),
        ],
        package_requirements=[],
    ),
    Node(
        description="Updates an existing item in the inventory",
        name="update_inventory_item",
        input_params=[
            Parameter(
                prama_type="str", name="item_id", description="ID of the inventory item"
            ),
            Parameter(
                prama_type="int",
                name="quantity",
                description="New quantity of the item",
                optional=True,
            ),
            Parameter(
                prama_type="float",
                name="price",
                description="New price of the item",
                optional=True,
            ),
        ],
        output_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item update",
            )
        ],
        package_requirements=[],
    ),
    Node(
        name="response_node_update",
        description="Returns confirmation of item update",
        input_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item update",
            )
        ],
        output_params=[],
        package_requirements=[],
    ),
]

# Execution Path 3: Deleting Inventory Items

execution_path_3 = [
    Node(
        description="Takes in the ID of the inventory item to be deleted",
        name="request_node_delete",
        input_params=None,
        output_params=[
            Parameter(
                prama_type="str", name="item_id", description="ID of the inventory item"
            )
        ],
        package_requirements=[],
    ),
    Node(
        description="Deletes an item from the inventory",
        name="delete_inventory_item",
        input_params=[
            Parameter(
                prama_type="str", name="item_id", description="ID of the inventory item"
            )
        ],
        output_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item deletion",
            )
        ],
        package_requirements=[],
    ),
    Node(
        name="response_node_delete",
        description="Returns confirmation of item deletion",
        input_params=[
            Parameter(
                prama_type="str",
                name="confirmation",
                description="Confirmation of item deletion",
            )
        ],
        output_params=[],
        package_requirements=[],
    ),
]

# Execution Path 4: Tracking Stock Levels

execution_path_4 = [
    Node(
        description="Requests the tracking of inventory stock levels",
        name="request_node_track",
        input_params=None,
        output_params=[],
        package_requirements=[],
    ),
    Node(
        description="Tracks and returns current stock levels of inventory items",
        name="track_stock_levels",
        input_params=[],
        output_params=[
            Parameter(
                prama_type="List[DataFrame]",
                name="stock_levels",
                description="Current stock levels of all inventory items",
            )
        ],
        package_requirements=["pandas"],
    ),
    Node(
        name="response_node_track",
        description="Returns the current stock levels of inventory items",
        input_params=[
            Parameter(
                prama_type="List[DataFrame]",
                name="stock_levels",
                description="Current stock levels of all inventory items",
            )
        ],
        output_params=[],
        package_requirements=[],
    ),
]
