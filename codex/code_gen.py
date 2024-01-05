import ast
import os
import re
import tempfile
import zipfile
from typing import List

from .model import FunctionData


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
                f"from service_{idx} import {function_data.function_name}\n"
            )
            # Generate Pydantic models and endpoint
            if len(params) > 1:
                # Create Pydantic model for request
                request_model = f"class RequestModel{idx}(BaseModel):\n"
                request_model += "\n".join([f"    {param}: str" for param in params])

                # Create Pydantic model for response if return type is provided
                response_model = ""
                if return_type:
                    response_model = f"\nclass ResponseModel{idx}(BaseModel):\n    result: {return_type}\n"

                # Add to endpoint functions
                endpoint_functions += f"""
{request_model}
{response_model}

@app.post("/{sanitized_endpoint_name}", response_model=ResponseModel{idx} if '{response_model}' else None)
def endpoint_{idx}(request: RequestModel{idx}):
    result = {function_data.function_name}(**request.dict())
    return {{'result': result}} if '{response_model}' else result
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
