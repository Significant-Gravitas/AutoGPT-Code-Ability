# Develop Prompts

We should probably have a process of refining these in order. So we would first see if we can update our base prompt to be clearer, then we work not the examples, and only if we still need to, do we add incantations as a last resort

## Summary of Variables

Variables are used across the template files to dynamically insert specific elements, such as function names, descriptions, and code snippets, into the generated output. Here's a summary of these variables, ordered by the file they are found in:

### `python.system.incantations.j2`
- `allow_stub`: A boolean indicating whether or not to allow stub functions in the generated code.

### `python.user.j2`
- `function_name`: The name of the function to be implemented.
- `function_signature`: The exact signature of the function that needs to be implemented.
- `goal`: The broader goal or context in which the function will be used.
- `provided_functions`: Functions provided for reuse within the new function implementation, if any.

### `python.retry.j2`
- `function_name`: The name of the main function.
- `description`: A description or code snippet that describes what the function does.
- `generation`: The generated response or output from the function.
- `error`: Any error messages that might have occurred during the generation process.


## File Descriptions

### `python.retry.j2`
Defines a template for retry mechanisms, capturing the main function's name, code or description, generated response, and any errors.

### `python.system.base.j2`
Lays out the structure for Python functions that adhere to simplicity and core Python libraries, guiding the creation of clear and implementable requirements and code templates.

### `python.system.examples.j2`
Provides example outputs for functions, showcasing how to verify URLs, download page content, convert HTML to Markdown, and more, with fully detailed doc strings for clarity.

### `python.system.incantations.j2`
Discusses the approach to solving problems with Python code, emphasizing the analysis, use of core Python objects, and guidelines for generating functional code with minimal stubs.

### `python.system.j2`
Combines the base template, examples, and incantations to guide the generation of functional Python code for specific tasks, emphasizing clarity and simplicity.

### `python.user.j2`
Focuses on creating a working code implementation for a specified function, including its signature and the goal it serves, while allowing for the reuse of provided functions without the need for rewriting.
