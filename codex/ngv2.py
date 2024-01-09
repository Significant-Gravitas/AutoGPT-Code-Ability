from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class BaseNode(BaseModel):
    id: str
    type: str
    inputs: Optional[Dict[str, str]]
    outputs: Optional[Dict[str, str]]


class StartNode(BaseNode):
    next: str


class ForEachNode(BaseNode):
    collection: str
    body: str
    next: str


class IfNode(BaseNode):
    condition: str
    trueNext: str
    falseNext: str


class SwitchNode(BaseNode):
    switchOn: str
    cases: Dict[str, str]
    default: str


class ActionNode(BaseNode):
    action: str
    next: str


class EndNode(BaseNode):
    pass


Node = Union[StartNode, ForEachNode, IfNode, SwitchNode, ActionNode, EndNode]


class NodeGraph(BaseModel):
    nodes: List[Node]
