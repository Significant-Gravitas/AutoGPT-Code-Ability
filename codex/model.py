import uuid
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel


class Parameter(BaseModel):
    """
    Represents a parameter with its type, name, and description.
    """

    prama_type: str
    name: str
    description: str
    optional: bool = False

    def __str__(self):
        return f"{self.name}: {self.prama_type} - {self.description}"


class Node(BaseModel):
    """
    Represents a node in the system.

    Attributes:
        description (str): The description of the node.
        name (str): The name of the node.
        input_pramas (List[Parameter] | None): The input params of the node.
        output_pramas (List[Parameter] | None): The output params of the node.
        package_requirements (List[str] | None): package requirements.
    """

    description: str
    name: str
    input_params: Optional[List[Parameter]]
    output_params: Optional[List[Parameter]]
    package_requirements: Optional[List[str]]

    def __str__(self) -> str:
        out = f"def {self.name}("
        if self.input_params:
            for param in self.input_params:
                out += f"{param.name}: {param.prama_type}, "
            out = out[:-2]
        out += ")"
        if self.output_params:
            out += " -> ("
            for param in self.output_params:
                out += f"{param.name}: {param.prama_type}, "
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
        out = "def request("
        if self.output_params:
            for param in self.output_params:
                out += f"{param.name}: {param.prama_type}, "
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
                out += f"    return {input_names_map[self.input_params[0].name]}"
            else:
                out += "    return ("
                for param in self.input_params:
                    out += f"{input_names_map[param.name] if param.name in input_names_map.keys() else param.name}, "
                out = out[:-2]
                out += ")"
        return out
