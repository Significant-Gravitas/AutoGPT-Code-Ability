import uuid
from typing import Dict, List, Optional, Tuple

from pgvector.sqlalchemy import Vector  # type: ignore
from pydantic import BaseModel
from sqlmodel import Column, Field, Relationship, SQLModel  # type: ignore


# Define the Pydantic model for function data
class FunctionData(BaseModel):
    function_name: str
    code: str
    requirements_txt: str
    endpoint_name: str


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

    required_packages: Optional[List[RequiredPackage]] = Relationship(
        back_populates="node"
    )

    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(768))
    )

    # Relationship definitions
    input_params: Optional[List[InputParameter]] = Relationship(back_populates="node")
    output_params: Optional[List[OutputParameter]] = Relationship(back_populates="node")

    code: Optional[str] = Field(default=None)

    quality: Optional[float] = Field(default=None)

    # def model_post_init(self, __context: Any) -> None:
    #     embedder = SentenceTransformer("all-mpnet-base-v2")
    #     self.embedding = embedder.encode(  # type: ignore
    #         self.description, normalize_embeddings=True, convert_to_numpy=True
    #     )

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

    def to_code(self, input_names_map: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
        """
        Converts the Node object to Python code.

        Args:
            input_names_map (Dict[str, str]): A dictionary mapping input
            parameter names to their corresponding names in the code.

        Returns:
            Tuple[str, Dict[str, str]]: A tuple containing the generated code
            and a dictionary mapping unique output parameter names to
            their corresponding names in the code.
        """
        unique_output_names_map: Dict[str, str] = {}
        out = "    "
        if self.output_params:
            for output_param in self.output_params:
                unique_chars = uuid.uuid4().hex[:4]
                out += f"{output_param.name}_{unique_chars}, "
                unique_output_names_map[
                    output_param.name
                ] = f"{output_param.name}_{unique_chars}"

            out = out[:-2]
            out += " = "
        out += f"{self.name}("
        if self.input_params:
            for input_param in self.input_params:
                in_name = (
                    input_names_map[input_param.name]
                    if input_param.name in input_names_map.keys()
                    else input_param.name
                )
                out += f"{in_name}, "
            out = out[:-2]
        out += ")"
        return (out, unique_output_names_map)

    def request_to_code(self) -> str:
        """
        Generates the code for the request function.

        Returns:
            str: The generated code for the request function.
        """
        out = f"def {self.name.lower()}("
        if self.output_params:
            for param in self.output_params:
                out += f"{param.name}: {param.param_type}, "
            out = out[:-2]
        out += "):\n"
        return out

    def response_to_code(self, input_names_map: Dict[str, str]) -> str:
        """
        Generates the code for the response function.

        Args:
            input_names_map (Dict[str, str]): A dictionary mapping input
            parameter names to their corresponding names in the code.

        Returns:
            str: The generated code for the response function.
        """
        out = ""
        if self.input_params:
            if len(self.input_params) == 1:
                out += f"    return {input_names_map[self.input_params[0].name] if input_names_map[self.input_params[0].name] else self.input_params[0].name}"
            else:
                out += "    return ("
                for param in self.input_params:
                    out += f"{input_names_map[param.name] if param.name in input_names_map.keys() else param.name}, "
                out = out[:-2]
                out += ")"
        return out
