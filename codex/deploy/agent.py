import ast
import base64
import logging
import uuid
from typing import Tuple

import black
import isort
from prisma.models import CompiledRoute as CompiledRouteDBModel
from prisma.models import CompletedApp, Deployment
from prisma.types import DeploymentCreateInput

from codex.api_model import Identifiers
from codex.deploy.model import Application
from codex.deploy.packager import create_zip_file

logger = logging.getLogger(__name__)


async def create_deployment(ids: Identifiers, completedApp: CompletedApp) -> Deployment:
    app = create_server_code(completedApp)

    zip_file = create_zip_file(app)
    file_name = completedApp.name.replace(" ", "_")

    try:
        base64.b64encode(zip_file)
        logger.info(f"Creating deployment for {completedApp.name}")
        encoded_file_bytes = base64.b64encode(zip_file).decode("utf-8")
        deployment = await Deployment.prisma().create(
            data=DeploymentCreateInput(
                CompletedApp={"connect": {"id": completedApp.id}},
                User={"connect": {"id": ids.user_id}},
                fileName=f"{file_name}.zip",
                fileSize=len(zip_file),
                # I need to do this as the Base64 type in prisma is not working
                fileBytes=encoded_file_bytes,  # type: ignore
            )
        )
    except Exception as e:
        logger.exception("Error creating deployment in database")
        raise ValueError(f"Error creating deployment in database: {e}")
    return deployment


def create_server_code(completed_app: CompletedApp) -> Application:
    """
    Args:
        application (Application): _description_

    Returns:
        Application: _description_
    """
    name = completed_app.name
    desc = completed_app.description

    server_code_imports = [
        "from fastapi import FastAPI",
        "from fastapi.responses import JSONResponse",
        "import logging",
        "import io",
        "from typing import *",
    ]
    server_code_header = f"""logger = logging.getLogger(__name__)

app = FastAPI(title="{name}", description='''{desc}''')"""

    service_routes_code = []
    if completed_app.CompiledRoutes is None:
        raise ValueError("Application must have at least one compiled route.")

    packages = []
    main_function_names = set()
    for i, compiled_route in enumerate(completed_app.CompiledRoutes):
        if compiled_route.ApiRouteSpec is None:
            raise ValueError(f"Compiled route {compiled_route.id} has no APIRouteSpec")

        if compiled_route.Packages:
            packages.extend(compiled_route.Packages)
        request = compiled_route.ApiRouteSpec.RequestObject
        response = compiled_route.ApiRouteSpec.ResponseObject

        assert request is not None, f"RequestObject is required for {compiled_route.id}"
        assert (
            response is not None
        ), f"ResponseObject is required for {compiled_route.id}"

        route_path = compiled_route.ApiRouteSpec.path
        logger.info(f"Creating route for {route_path}")
        # import the main function from the service file
        compiled_route_module = compiled_route.fileName.replace(".py", "")
        service_import = f"from {compiled_route_module} import *"
        server_code_imports.append(service_import)

        # Write the api endpoint
        # TODO: pass the request method from the APIRouteSpec
        response_type = "return JSONResponse(content=response)"
        # horrible if if if for type checking
        if response.Fields:
            params = response.Fields
            if (len(params) > 0) and (params[0].typeName == "bytes"):
                response_type = """
    # Convert the bytes to a BytesIO object for streaming
    file_stream = io.BytesIO(response)

    # Set the correct content-type for zip files
    headers = {
        "Content-Disposition": f"attachment; filename="new_file.zip""
    }

    # Return the streaming response
    return StreamingResponse(
        content=file_stream, media_type="application/zip", headers=headers
    )
"""
        assert request.Fields is not None, f"RequestObject {request.id} has no Fields"

        request_param_str = ", ".join(
            [f"{param.name}: {param.typeName}" for param in request.Fields]
        )
        param_names_str = ", ".join([param.name for param in request.Fields])

        # method is a string here even though it should be an enum in the model
        method_name = compiled_route.ApiRouteSpec.method.lower()  # type: ignore
        api_route_name = f"{method_name}_{compiled_route.mainFunctionName}_route"
        if compiled_route.mainFunctionName in main_function_names:
            main_function_names.add(compiled_route.mainFunctionName)

            unique_end = uuid.uuid4().hex[:2]
            api_route_name += f"_{unique_end}"

        route_code = f"""@app.{method_name}("{route_path}")
async def {api_route_name}({request_param_str}):
    try:
        response = {compiled_route.mainFunctionName}({param_names_str})
    except Exception as e:
        logger.exception("Error processing request")
        response = dict()
        response["error"] =  str(e)
        return JSONResponse(content=response)
    {response_type}
"""
        service_routes_code.append(route_code)

    # Compile the server code
    server_code = "\n".join(server_code_imports)
    server_code += "\n\n"
    server_code += server_code_header
    server_code += "\n\n"
    server_code += "\n\n".join(service_routes_code)

    # Update the application with the server code
    sorted_content = isort.code(server_code)
    formatted_code = black.format_str(sorted_content, mode=black.FileMode())
    return Application(
        name=name,
        description=desc,
        server_code=formatted_code,
        completed_app=completed_app,
        packages=packages,
    )
