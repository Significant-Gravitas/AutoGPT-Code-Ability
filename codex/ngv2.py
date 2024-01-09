from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class BaseNode(BaseModel):
    id: str
    type: str
    description: str
    inputs: Optional[Dict[str, str]] = {}
    outputs: Optional[Dict[str, str]] = {}

class StartNode(BaseNode):
    type: str = 'start'
    next: Optional['Node']

class ForEachNode(BaseNode):
    type: str = 'forEach'
    collection: str
    body: Optional['Node']
    next: Optional['Node']

class IfNode(BaseNode):
    type: str = 'if'
    condition: str
    trueNext: Optional['Node']
    falseNext: Optional['Node']

class SwitchNode(BaseNode):
    type: str = 'switch'
    switchOn: str
    cases: Dict[str, 'Node']
    default: Optional['Node']

class ActionNode(BaseNode):
    type: str = 'action'
    action: str
    next: Optional['Node']

class EndNode(BaseNode):
    type: str = 'end'

# Union of all node types
Node = Union[StartNode, ForEachNode, IfNode, SwitchNode, ActionNode, EndNode]
BaseNode.model_rebuild()

# Node graph class
class NodeGraph(BaseModel):
    nodes: List[Node]



# Create an example node graph
# Create an example node graph
example_graph = NodeGraph(
    nodes=[
        StartNode(
            id="start",
            description="Start of the script",
            type="start",
            outputs={"url": "User provided URL"},
            next=ActionNode(
                id="fetchPage",
                description="Fetch the webpage from the URL",
                type="action",
                action="fetch webpage",
                inputs={"url": "start.url"},
                outputs={"webpage": "fetched web content"},
                next=SwitchNode(
                    id="formatSelection",
                    description="Determine output format",
                    type="switch",
                    switchOn="user selected format",
                    cases={
                        "Markdown": "convertToMarkdown",
                        "HTML": "returnHTML",
                        "RTF": "convertToRTF"
                    },
                    default="returnHTML"
                )
            )
        ),
        ActionNode(
            id="convertToMarkdown",
            description="Convert webpage to Markdown",
            type="action",
            action="convert to Markdown",
            inputs={"webpage": "fetchPage.webpage"},
            next=EndNode(
                id="endMarkdown",
                description="End of the script for Markdown",
                type="end"
            )
        ),
        ActionNode(
            id="returnHTML",
            description="Return webpage as HTML",
            type="action",
            action="return HTML",
            inputs={"webpage": "fetchPage.webpage"},
            next=EndNode(
                id="endHTML",
                description="End of the script for HTML",
                type="end"
            )
        ),
        ActionNode(
            id="convertToRTF",
            description="Convert webpage to RTF",
            type="action",
            action="convert to RTF",
            inputs={"webpage": "fetchPage.webpage"},
            next=EndNode(
                id="endRTF",
                description="End of the script for RTF",
                type="end"
            )
        )
    ]
)



# Output the example graph as JSON string
example_graph_json = example_graph.model_dump()
from pprint import pprint
pprint(example_graph_json, indent=2)