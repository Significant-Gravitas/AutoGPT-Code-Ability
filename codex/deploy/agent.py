import ast
import logging

import black
import isort
from prisma.models import CompiledRoute as CompiledRouteDBModel
from prisma.models import CompletedApp

from codex.deploy.model import Application, CompiledRoute
from codex.developer.model import Package

logger = logging.getLogger(__name__)


def compile_application(app: CompletedApp) -> Application:
    """
    Packages the app for delivery
    """
    try:
        compiled_routes = {}
        packages = []
        for db_compiled_route in app.compiledRoutes:
            logger.info(
                f"Compiling route {db_compiled_route.apiRouteSpec.path}. Num Functions: { len(db_compiled_route.functions)}"
            )
            for function in db_compiled_route.functions:
                if function.packages:
                    for pack in function.packages:
                        packages.append(
                            Package(
                                package_name=pack.packageName,
                                version=pack.version,
                                specifier=pack.specifier,
                            )
                        )
            compiled_routes[db_compiled_route.apiRouteSpec.path] = compile_route(
                db_compiled_route
            )

        app = Application(
            name=app.name,
            description=app.description,
            server_code="",
            routes=compiled_routes,
            packages=packages,
        )
    except Exception as e:
        logger.exception("Error compiling application")
        raise e

    return create_server_code(app)


def create_server_code(application: Application) -> Application:
    """
    Args:
        application (Application): _description_

    Returns:
        Application: _description_
    """
    server_code_imports = [
        "from fastapi import FastAPI",
        "from fastapi.responses import JSONResponse",
        "import logging",
        "from typing import *",
    ]
    server_code_header = f"""logger = logging.getLogger(__name__)\n\napp = FastAPI(title="{application.name}", description="{application.description}")"""
    service_routes_code = []
    for route_path, compiled_route in application.routes.items():
        logger.info(f"Creating route for {route_path}")
        # import the main function from the service file
        service_import = f"from project.{compiled_route.service_file_name.replace('.py', '')} import *"
        server_code_imports.append(service_import)

        # Write the api endpoint
        # TODO: pass the request method
        route_code = f"""@app.post("{route_path}")
async def {compiled_route.main_function_name}_route({compiled_route.request_param_str}):
    try:
        response = {compiled_route.main_function_name}({compiled_route.param_names_str})
    except Exception as e:
        logger.exception("Error processing request")
        response = dict()
        response["error"] =  str(e)
    return JSONResponse(content=response)
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
    return application.copy(update={"server_code": formatted_code})


def compile_route(compiled_route: CompiledRouteDBModel) -> CompiledRoute:
    """
    Packages the route for delivery
    """

    packages = []
    imports = []
    rest_of_code_sections = []
    for i, function in enumerate(compiled_route.functions):
        logger.info(
            f"{i+1}/{len(compiled_route.functions)} Compiling function {function.name}"
        )
        import_code, rest_of_code = extract_imports(function.code)
        imports.append(import_code)
        rest_of_code_sections.append(rest_of_code)
        if function.packages:
            packages.extend(function.packages)

    import_code, main_function = extract_imports(compiled_route.codeGraph.code_graph)
    req_param_str, param_names_str = extract_request_params(
        compiled_route.codeGraph.code_graph
    )
    imports.append(import_code)

    output_code = "\n".join(imports)
    output_code += "\n\n"
    output_code += "\n\n".join(rest_of_code_sections)
    output_code += "\n\n"
    output_code += main_function

    sorted_content = isort.code(output_code)

    formatted_code = black.format_str(sorted_content, mode=black.FileMode())

    return CompiledRoute(
        service_code=formatted_code,
        service_file_name=compiled_route.codeGraph.function_name.strip().replace(
            " ", "_"
        )
        + "_service.py",
        main_function_name=compiled_route.codeGraph.function_name,
        request_param_str=req_param_str,
        param_names_str=param_names_str,
        packages=packages,
    )


def extract_request_params(main_function_code: str) -> str:
    """
    Extracts the request params from the main function code.

    Example Return:
        'id: int, name: str'
    """
    tree = ast.parse(main_function_code)

    params = []
    param_names = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                param_name = arg.arg
                # Default to 'Any' or another placeholder if you prefer
                type_annotation = "Any"
                if arg.annotation:
                    type_annotation = ast.unparse(arg.annotation)
                params.append(f"{param_name}: {type_annotation}")
                param_names.append(param_name)
            break

    params_annotations = ", ".join(params)
    param_names_str = ", ".join(param_names)
    return params_annotations, param_names_str


def extract_imports(function_code: str) -> (str, str):
    """
    Extracts the imports from the function code and returns them along with the rest of the code,
    excluding the import statements.
    """
    # Parse the function code to an AST
    tree = ast.parse(function_code)

    # Lists to hold import nodes and non-import nodes
    import_nodes = []
    non_import_nodes = []

    # Separate the nodes into import and non-import lists
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_nodes.append(node)
        else:
            non_import_nodes.append(node)

    # Unparse the nodes to recreate the sections
    imports_section = "\n".join(ast.unparse(node) for node in import_nodes)
    rest_of_code = "\n".join(ast.unparse(node) for node in non_import_nodes)

    return imports_section, rest_of_code
