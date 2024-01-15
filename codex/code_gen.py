import ast
import logging
import os
import re
import tempfile
import zipfile
from enum import Enum
from typing import List

from pydantic import BaseModel

from .chains.gen_branching_graph import ElseIf, NodeDef, NodeGraph, NodeTypeEnum
from .model import FunctionData

logger = logging.getLogger(__name__)


class CodeablrNodeTypeEnum(Enum):
    START = "start"
    IF = "if"
    ELIF = "elif"
    ELSE = "else"
    ACTION = "action"
    END = "end"


class CodeableNode(BaseModel):
    intent_level: int
    node_type: CodeablrNodeTypeEnum
    node: NodeDef | None = None
    elseif: ElseIf

    def __str__(self):
        if self.node_type == CodeablrNodeTypeEnum.START:
            out = f"def {self.name}("
            if self.output_params:
                for param in self.output_params:
                    out += f"{param.name}: {param.param_type}, "
                out = out[:-2]
            out += "):"
            return out
        elif self.node_type == CodeablrNodeTypeEnum.IF:
            return f"if {self.node.python_if_condition}:"
        elif self.node_type == CodeablrNodeTypeEnum.ELIF:
            return f"elif {self.elseif.python_condition}:"
        elif self.node_type == CodeablrNodeTypeEnum.ELSE:
            return "else:"
        elif self.node_type == CodeablrNodeTypeEnum.ACTION:
            out = ""
            if self.node.output_params:
                for output_param in self.node.output_params:
                    out += f"{output_param.name}, "
                out = out[:-2]
                out += " = "
            out += f"{self.name}("
            if self.node.input_params:
                for input_param in self.node.input_params:
                    out += f"{input_param.name}, "
                out = out[:-2]
            out += ")"
            return out
        elif self.node_type == CodeablrNodeTypeEnum.END:
            out = ""
            if self.node.input_params:
                if len(self.node.input_params) == 1:
                    out += f"return {self.node.input_params[0].name}"
                else:
                    out += "return ("
                    for param in self.node.input_params:
                        out += f"{param.name}, "
                    out = out[:-2]
                    out += ")"
            return out
        else:
            raise ValueError(f"Invalid node type: {self.node_type}")


def convert_graph_to_code(node_graph: NodeGraph) -> str:
    codeable_nodes = pre_process_nodes(node_graph)
    return graph_to_code(codeable_nodes)


def pre_process_nodes(node_graph: NodeGraph) -> List[CodeableNode]:
    codeable_nodes = []

    # Preprocess the node graph to resolve if branching
    skip_node = []
    indent_level = 0
    for i, node in enumerate(node_graph.nodes):
        if node.id in skip_node:
            continue
        if node.node_type == NodeTypeEnum.START:
            codeable_nodes.append(
                CodeableNode(
                    intent_level=indent_level,
                    node_type=CodeablrNodeTypeEnum.START,
                    node=node,
                )
            )
            indent_level += 1
        elif node.node_type == NodeTypeEnum.IF:
            commonon_descendent = find_common_descendent(node_graph, node, i)
            codeable_nodes.append(
                CodeableNode(
                    intent_level=indent_level,
                    node_type=CodeablrNodeTypeEnum.IF,
                    node=node,
                )
            )
            skip, code = process_if_paths(
                node_graph.nodes,
                node,
                node.true_next_node_id,
                commonon_descendent,
                indent_level + 1,
            )
            skip_node.extend(skip)
            codeable_nodes.extend(code)
            for elifs in node.elifs:
                codeable_nodes.append(
                    CodeableNode(
                        intent_level=indent_level,
                        node_type=CodeablrNodeTypeEnum.ELIF,
                        node=None,
                        elseif=elifs,
                    )
                )
                skip, code = process_if_paths(
                    node_graph.nodes,
                    node,
                    elifs.true_next_node_id,
                    commonon_descendent,
                    indent_level + 1,
                )
                skip_node.extend(skip)
                codeable_nodes.extend(code)
            codeable_nodes.append(
                CodeableNode(
                    intent_level=indent_level,
                    node_type=CodeablrNodeTypeEnum.ELSE,
                    node=node,
                )
            )
            skip, code = process_if_paths(
                node_graph.nodes,
                node,
                node.false_next_node_id,
                commonon_descendent,
                indent_level + 1,
            )
            skip_node.extend(skip)
            codeable_nodes.extend(code)
        elif node.node_type == NodeTypeEnum.ACTION:
            codeable_nodes.append(
                CodeableNode(
                    intent_level=indent_level,
                    node_type=CodeablrNodeTypeEnum.ACTION,
                    node=node,
                )
            )
        elif node.node_type == NodeTypeEnum.END:
            codeable_nodes.append(
                CodeableNode(
                    intent_level=indent_level,
                    node_type=CodeablrNodeTypeEnum.END,
                    node=node,
                )
            )
            indent_level -= 1

    return codeable_nodes


def graph_to_code(codeable_nodes: List[CodeableNode]) -> str:
    code = ""
    indent_str = "    "
    for node in codeable_nodes:
        code += indent_str * node.intent_level + str(node) + "\n"
    return code


def process_if_paths(
    nodes: List[NodeDef],
    node: NodeDef,
    next_node_id: str,
    commonon_descendent: str,
    intent_level: int,
) -> List[CodeableNode]:
    codeable_nodes = []
    skip_nodes = []
    next_node = node.true_next_node_id
    for subnode in nodes:
        if subnode.id == commonon_descendent:
            break
        if subnode.id == next_node:
            codeable_nodes.append(
                CodeableNode(intent_level=2, node_type=subnode.node_type, node=subnode)
            )
            skip_nodes.append(subnode.id)
            next_node = subnode.next_node_id
    return skip_nodes, codeable_nodes


def find_common_descendent(node_graph: NodeGraph, node: NodeDef, i: int) -> str:
    commonon_descendent = ""
    descendents = []
    for subnode in node_graph.nodes[i + 1 :]:
        if subnode.id in descendents and subnode.next_node_id:
            commonon_descendent = subnode.id
        commonon_descendent.append(subnode.next_node_id)


def analyze_function_signature(code: str, function_name: str):
    # Parse the code into an AST (Abstract Syntax Tree)
    tree = ast.parse(code)

    # Find the definition of the function
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Extract the parameters
            params = [arg.arg for arg in node.args.args]

            # Check for return annotation
            return_type = None
            if node.returns:
                # Convert the return type node to string
                return_type = ast.dump(node.returns, annotate_fields=False)

            return params, return_type

    return None, None


def create_fastapi_server(functions_data: List[FunctionData]) -> bytes:
    """
    Create a FastAPI server with multiple endpoints using a list of Pydantic objects for function data.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        combined_requirements = set(["fastapi\n", "uvicorn\n", "pydantic\n"])
        import_statements = "from fastapi import FastAPI, Body\nfrom pydantic import BaseModel\n\napp = FastAPI()\n"
        endpoint_functions = ""

        # Process each function data Pydantic object
        for idx, function_data in enumerate(functions_data):
            # Analyze the function
            params, return_type = analyze_function_signature(
                function_data.code, function_data.function_name
            )
            if not params:
                logger.error(
                    f"Function {function_data.function_name} has no parameters: Details:\n {function_data.code}"
                )
                raise ValueError(
                    f"Function {function_data.function_name} has no parameters"
                )

            # Sanitize the endpoint name
            sanitized_endpoint_name = re.sub(
                r"\W|^(?=\d)", "_", function_data.endpoint_name
            )

            # Write the code to a uniquely named service file
            service_file_name = f"service_{idx}.py"
            service_file_path = os.path.join(temp_dir, service_file_name)
            with open(service_file_path, "w") as service_file:
                service_file.write(function_data.code)

            # Import statement for the function
            import_statements += (
                f"from .service_{idx} import {function_data.function_name}\n"
            )

            # Generate Pydantic models and endpoint
            if len(params) > 1:
                # Create Pydantic model for request
                request_model = f"class RequestModel{idx}(BaseModel):\n"
                request_model += "\n".join([f"    {param}: str" for param in params])

                # Add to endpoint functions
                endpoint_functions += f"""
{request_model}

@app.post("/{sanitized_endpoint_name}")
def endpoint_{idx}(request: RequestModel{idx}):
    result = {function_data.function_name}(**request.dict())
    return result
"""
            else:
                # Generate endpoint without Pydantic models
                params_str = ", ".join([f"{param}: str" for param in params])
                endpoint_functions += f"""
@app.get("/{sanitized_endpoint_name}")
def endpoint_{idx}({params_str}):
    return {function_data.function_name}({', '.join(params)})
"""

            # Add requirements
            combined_requirements.update(function_data.requirements_txt.splitlines())

        # Write server.py with imports at the top
        server_file_path = os.path.join(temp_dir, "server.py")
        with open(server_file_path, "w") as server_file:
            server_file.write(import_statements + endpoint_functions)

        # Write combined requirements to requirements.txt
        requirements_file_path = os.path.join(temp_dir, "requirements.txt")
        with open(requirements_file_path, "w") as requirements_file:
            requirements_file.write("\n".join(combined_requirements))

        # Create a zip file of the directory
        zip_file_path = os.path.join(temp_dir, "server.zip")
        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "server.zip":
                        continue
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, temp_dir))

        # Read and return the bytes of the zip file
        with open(zip_file_path, "rb") as zipf:
            zip_bytes = zipf.read()

    return zip_bytes
