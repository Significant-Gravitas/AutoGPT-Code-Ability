from enum import Enum
from typing import List, Optional

from pgvector.sqlalchemy import Vector  # type: ignore
from langchain.pydantic_v1 import BaseModel
from sqlmodel import Column, Field, Relationship, SQLModel  # type: ignore
from codex.chains.gen_branching_graph import NodeGraph


# Define the Pydantic model for function data
class FunctionData(BaseModel):
    function_name: str
    code: str
    requirements_txt: str
    endpoint_name: str
    graph: NodeGraph

    class Config:
        arbitrary_types_allowed = True


class NodeTypeEnum(Enum):
    START = "start"
    IF = "if"
    ACTION = "action"
    END = "end"


class OutputParameter(SQLModel, table=True):
    """
    Represents a parameter with its type, name, and description.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    param_type: str
    name: str
    description: str
    optional: bool = False

    node_id: Optional[int] = Field(default=None, foreign_key="node.id")
    node: Optional["Node"] = Relationship(back_populates="output_params")

    def __str__(self):
        return f"{self.name}: {self.param_type} - {self.description}"


class InputParameter(SQLModel, table=True):
    """
    Represents a parameter with its type, name, and description.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    param_type: str
    name: str
    description: str
    optional: bool = False

    node_id: Optional[int] = Field(default=None, foreign_key="node.id")
    node: Optional["Node"] = Relationship(back_populates="input_params")

    def __str__(self):
        return f"{self.name}: {self.param_type} - {self.description}"


class RequiredPackage(SQLModel, table=True):
    """
    Represents a required package.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    package_name: str
    version: Optional[str] = Field(default=None)
    specifier: Optional[str] = Field(default=None)

    node_id: Optional[int] = Field(default=None, foreign_key="node.id")
    node: Optional["Node"] = Relationship(back_populates="required_packages")


# class NodeGraphModel(SQLModel, table=True):
#     """
#     Represents a node graph.
#     """

#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     description: str

#     node_graph: str
#     code: str

#     required_packages: Optional[List[RequiredPackage]] = Relationship(
#         back_populates="node"
#     )

#     nodes: Optional[List["Node"]] = Relationship(back_populates="node_graph")


class Node(SQLModel, table=True):
    """
    Represents a node in the system.

    Attributes:
        description (str): The description of the node.
        name (str): The name of the node.
        input_params (List[Parameter] | None): The input params of the node.
        output_params (List[Parameter] | None): The output params of the node.
        package_requirements (List[str] | None): package requirements.
        embedding (Vector): The embedding field for pg vector.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    name: str
    node_type: str

    required_packages: Optional[List[RequiredPackage]] = Relationship(
        back_populates="node"
    )

    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(1536))
    )

    # Relationship definitions
    input_params: Optional[List[InputParameter]] = Relationship(back_populates="node")
    output_params: Optional[List[OutputParameter]] = Relationship(back_populates="node")

    code: Optional[str] = Field(default=None)

    quality: Optional[float] = Field(default=None)

    def __str__(self) -> str:
        out = f"def {self.name}("
        if self.input_params:
            for param in self.input_params:
                out += f"{param.name}: {param.param_type}, "
            out = out[:-2]
        out += ")"
        if self.output_params:
            out += " -> ("
            for param in self.output_params:
                out += f"{param.name}: {param.param_type}, "
            out = out[:-2]
            out += ")"
        out += ":"
        out += f"\n  {self.description}"
        if self.input_params:
            out += "\n  Input Parameters:"
            for param in self.input_params:
                out += f"\n    {param}"
        if self.output_params:
            out += "\n  Output Parameters:"
            for param in self.output_params:
                out += f"\n    {param}"
        return out
