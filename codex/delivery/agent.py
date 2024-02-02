import ast
import logging
from typing import List

import black
import isort

from codex.architect.model import CodeGraph
from codex.delivery.model import Application, CompiledRoute
from codex.requirements.model import ApplicationRequirements

logger = logging.getLogger(__name__)


def compile_application(
    application_requirement: ApplicationRequirements, code_graphs: List[CodeGraph]
) -> Application:
    """
    Packages the app for delivery

    NOTE: This agent will hopefull not reqire llm calls
    """
    compiled_routes = {}
    packages = []
    for route in code_graphs:
        compiled_route = compile_route(route)
        packages.extend(compiled_route.packages)
        compiled_routes[route.api_route] = compiled_route

    return Application(
        name=application_requirement.name,
        description=application_requirement.context,
        server_code="",
        routes=compiled_routes,
        packages=packages,
    )


def compile_route(code_graph: CodeGraph) -> CompiledRoute:
    """
    Packages the route for delivery
    """

    packages = []
    imports = []
    rest_of_code_sections = []
    for function in code_graph.functions:
        import_code, rest_of_code = extract_imports(function.code)
        imports.append(import_code)
        rest_of_code_sections.append(rest_of_code)
        packages.extend(function.packages)

    import_code, main_function = extract_imports(code_graph.code_graph)
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
        service_file_name=code_graph.function_name.strip().replace(" ", "_")
        + "_service.py",
        packages=packages,
    )


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
