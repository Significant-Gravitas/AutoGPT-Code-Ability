import ast
from langchain.pydantic_v1 import BaseModel

class Param(BaseModel):
    param_type: str
    name: str

class NodeDef(BaseModel):
    func_name: str
    args: list[Param]
    return_args: list[Param]


class FuncDefVisitor(ast.NodeVisitor):
    def __init__(self):
        self.type_hints = {}  # Dictionary to store variable types
        self.return_types = {}
        self.node_defs = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Unknown'
            args.append(f"{arg_name}: {arg_type}")
            self.type_hints[arg_name] = arg_type
        args_str = ', '.join(args)
        return_type = ast.unparse(node.returns) if node.returns else 'None'
        print(f"Function '{node.name}' definition ({args_str}) -> {return_type}:")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target_id = node.target.id
        target_type = ast.unparse(node.annotation)
        self.type_hints[target_id] = target_type
        if isinstance(node.value, ast.Call):
            self.return_types[node.value.func.id] = [Param(param_type=target_type, name=target_id)]
        value = self.process_value(node.value)
        if value:
            self.node_defs.append(value)

    def visit_Assign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.value, ast.Call):
            print(node.value.func.id)
            return_type = []
            for dim in node.targets[0].dims:
                return_type.append(
                    Param(
                        param_type=self.type_hints[dim.id],
                        name=dim.id
                    )
                )
            self.return_types[node.value.func.id] = return_type
        value = self.process_value(node.value)
        if value:
            self.node_defs.append(value)
            
    def process_value(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            func_name = self.process_value(node.func)

            args = [self.process_value(arg) for arg in node.args]
            arg_types = []
            for a in args:
                arg_types.append(
                    Param(
                        param_type=self.type_hints[a] if a in self.type_hints.keys() else 'Unknown',
                        name=a
                    )
                )
            # Attempt to infer return type from function call
            return_type = self.return_types.get(func_name, 'Unknown')
            return NodeDef(func_name=func_name, args=arg_types, return_args=return_type)

        elif isinstance(node, ast.Attribute):
            return f"{self.process_value(node.value)}.{node.attr}"

    # def visit_Call(self, node: ast.Call) -> None:
        
    #     func_name = self.process_value(node.func)
    #     args = [self.process_value(arg) for arg in node.args]
    #     args_str = ', '.join(args)
    #     # Attempt to infer return type from function call
    #     return_type = self.type_hints.get(func_name, 'Unknown')
    #     print(f"  Function call: {func_name}({args_str}) -> {return_type}")

def extract_function_definitions(code: str):
    tree = ast.parse(code)
    visitor = FuncDefVisitor()
    visitor.visit(tree)
    for node_def in visitor.node_defs:
        print(node_def)

code = """
def summarize_csv(file_path: str) -> dict:
    # Function to read CSV file and return its content
    csv_content = read_csv_file(file_path)
    
    # Function to validate the CSV structure and content
    is_valid_csv: bool = validate_csv_structure(csv_content)
    if not is_valid_csv:
        raise ValueError("Invalid CSV structure.")

    # Function to extract column headers from the CSV content
    headers: list = extract_column_headers(csv_content)
    
    # Function to parse each column in the CSV and extract the data
    column_data: dict = parse_csv_columns(csv_content)
    
    # Initialize a dictionary to hold the summary statistics
    summary_stats: dict = {}
    
    # Loop over each column and calculate summary statistics
    column_name: str
    for column_name in headers:
        # Function to calculate summary statistics for a single column
        stats: dict = calculate_column_statistics(column_data[column_name])
        summary_stats[column_name] = stats
    
    return summary_stats

"""
extract_function_definitions(code)

from typing import List

def convert_webpages(urls: List[str], format: str) -> List[str]:
    verified_urls: List[str] = check_urls(urls)

    output: List[str] = []
    for vurl in verified_urls:
        html: str = download_page(vurl)
        if format == 'markdown':
            md: str = convert_to_markdown(html)
            output.apppend(md)
        else:
            output.append(html)
    return output
