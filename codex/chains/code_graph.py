from langchain.pydantic_v1 import BaseModel
from typing import Dict, List
import ast
import logging
from typing import Dict, List

import ast
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class CodeGraph(BaseModel):
    name: str
    code_graph: str
    imports: List[str]
    functions: Dict[str, str]

code_model = ChatOpenAI(
    temperature=1,
    model_name="gpt-4-0125-preview",
    max_tokens=4095,
)
    
class CodeGraphVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}
        self.imports = []


    def visit_Import(self, node):
        for alias in node.names:
            import_line = f"import {alias.name}"
            if alias.asname:
                import_line += f" as {alias.asname}"
            self.imports.append(import_line)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            import_line = f"from {node.module} import {alias.name}"
            if alias.asname:
                import_line += f" as {alias.asname}"
            self.imports.append(import_line)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Unknown'
            args.append(f"{arg_name}: {arg_type}")
        args_str = ', '.join(args)
        return_type = ast.unparse(node.returns) if node.returns else 'None'
        print(f"Function '{node.name}' definition ({args_str}) -> {return_type}:")
        self.functions[node.name] = ast.unparse(node)
        self.generic_visit(node)

class CodeGraphParsingException(Exception):
    pass

class CodeGraphOutputParser(StrOutputParser):
    """OutputParser that parses LLMResult into the top likely string."""
    function_name: str

    @staticmethod
    def _sanitize_output(text: str):
        # Initialize variables to store requirements and code
        code = text.split("```python")[1].split("```")[0]
        logger.debug(f"Code: {code}")
        return code
    

    def parse(self, text: str) -> str:
        """Returns the input text with no changes."""
        code = CodeGraphOutputParser._sanitize_output(text)
        tree = ast.parse(code)
        visitor = CodeGraphVisitor()
        visitor.visit(tree)
        
        functions = visitor.functions.copy()
        del functions[self.function_name]
        
        return CodeGraph(
            name=self.function_name,
            code_graph=visitor.functions[self.function_name],
            imports=visitor.imports,
            functions=functions
        )
            

system_prompt = '''As an expert staff engineer. You write the structure of a problem in a python function that uses only stuff from only the core python libs, calling stub functions that you have designed to be simple enough for a junior developer to implement.

You always use types from the core python types: `bool`, `int`, `float`, `complex`, `str`, `bytes`, `tuple`, `list`, `dict`, `set`, `frozenset`.
 collection based param_types must be in the format: `list[int]`, `set[str]`, `tuple[float, str]`, etc.
You can use types from libraries when required.
You use pydantic objects for complex types

You always add a doc string to each function so the junior developer knows what to do.

Here is an example output for a function that takes in a list of urls and outputs the webpage as either a markdown or html file.

```
def check_urls(urls: list[str]) -> list[str]:
    """
    Verifies the validity and accessibility of a list of URLs.

    This function checks if the provided URLs are formatted correctly and are accessible.

    Args:
        urls (list[str]): A list of URLs to be verified.

    Returns:
        list[str]: A list of URLs that are verified to be valid and accessible.
    """
    pass

def download_page(url: str) -> str:
    """
    Downloads the HTML content of a given webpage.

    This function takes a URL and downloads the HTML content of the webpage at that URL.

    Args:
        url (str): The URL of the webpage to download.

    Returns:
        str: The HTML content of the webpage.
    """
    pass

def convert_to_markdown(html: str) -> str:
    """
    Converts HTML content to Markdown format.

    This function takes HTML content as input and converts it into Markdown format. 
    It's useful for transforming webpages into a more readable and simpler text format.

    Args:
        html (str): The HTML content to be converted.

    Returns:
        str: The content converted into Markdown format.
    """
   pass

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
```

Always start your answer with your analysis of the problem and possible problems. Then discuss the types of objects that maybe useful

NEVER USE ANY OR OBJ TYPES 
END YOUR REPLY AS SOON AS YOU FNISH THE CODE BLOCK
'''


def write_graph_chain(
    invoke_params: Dict = {}, max_retries: int = 5, attempts: int = 0
) -> str:
    """Returns the input text with no changes."""
    parser_write_node = CodeGraphOutputParser(function_name=invoke_params["function_name"])

    prompt_write_node = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "Main function name: {function_name}\n Description: {description}",
            ),
        ]
    )
    chain_write_graph = prompt_write_node | code_model | parser_write_node
    while attempts < max_retries:
        try:
            return chain_write_graph.invoke(
                invoke_params,
            )
        except Exception as e:
            attempts += 1
            logger.error(f"Error writing node: {e}")
            continue
        except CodeGraphParsingException as e:
            attempts += 1
            logger.error(f"Error validating code: {e}")
            continue
    raise ValueError(f"Error writing node after {max_retries} attempts.")


if __name__ == '__main__':

    cg = write_graph_chain({"function_name": "check_availability", "description": '''### **Overview**

The function is designed to return the real-time availability status of professionals, dynamically updated based on their current activity or schedule. It operates without the need for database access, relying instead on real-time or pre-set schedule data provided at the time of the query.

### **Input**

1. **Current Time:** The timestamp at which the availability status is being requested.
2. **Schedule Data:** A pre-set schedule for the professional, including start and end times of appointments or busy periods.

### **Process**

1. **Validation:** Check if the **Schedule** **Data** is valid and if the current time is provided in the correct format.
2. **Determine Availability:**
    - If schedule data is provided, the function compares the current time against the schedule to determine if the professional is currently in an appointment or busy period.
    - If no schedule data is provided, the function assumes the professional's status is assumed to be 'Available' .

### **Output**

1. **Availability Status:** A response indicating the professional's current availability status. The status can be:
    - 'Available' - The professional is free and can accept appointments.
    - 'Busy' - The professional is currently occupied and cannot accept appointments.'''})
    import IPython
    IPython.embed()