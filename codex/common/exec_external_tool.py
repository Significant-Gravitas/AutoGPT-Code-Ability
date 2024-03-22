import enum
import logging
import os
import subprocess
import tempfile

from codex.common.ai_block import ValidationError

logger = logging.getLogger(__name__)


class OutputType(enum.Enum):
    STD_OUT = "stdout"
    STD_ERR = "stderr"
    BOTH = "both"


def exec_external_on_contents(
    command_arguments: list[str],
    file_contents,
    suffix: str = ".py",
    output_type: OutputType = OutputType.BOTH,
    raise_file_contents_on_error: bool = False,
) -> str:
    """
    Execute an external tool with the provided command arguments and file contents
    :param command_arguments: The command arguments to execute
    :param file_contents: The file contents to execute the command on
    :param suffix: The suffix of the temporary file. Default is ".py"
    :return: The file contents after the command has been executed

    Note: The file contents are written to a temporary file and the command is executed
    on that file. The command arguments should be a list of strings, where the first
    element is the command to execute and the rest of the elements are the arguments to
    the command. There is no need to provide the file path as an argument, as it will
    be appended to the command arguments.

    Example:
    exec_external(["ruff", "check"], "print('Hello World')")
    will run the command "ruff check <temp_file_path>" with the file contents
    "print('Hello World')" and return the file contents after the command
    has been executed.

    """
    errors = ""
    if len(command_arguments) == 0:
        raise AssertionError("No command arguments provided")

    # Run ruff to validate the code
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(file_contents.encode("utf-8"))
        temp_file.flush()

        command_arguments.append(str(temp_file_path))

        # Run Ruff on the temporary file
        try:
            result = subprocess.run(
                args=command_arguments,
                capture_output=True,
                text=True,
            )
            logger.debug(f"Output: {result.stdout}")
            if temp_file_path in result.stdout:
                stdout = result.stdout  # .replace(temp_file.name, "/generated_file")
                logger.debug(f"Errors: {result.stderr}")
                if output_type == OutputType.STD_OUT:
                    errors = stdout
                elif output_type == OutputType.STD_ERR:
                    errors = result.stderr
                else:
                    errors = stdout + "\n" + result.stderr

            with open(temp_file_path, "r") as f:
                file_contents = f.read()
        finally:
            # Ensure the temporary file is deleted
            os.remove(temp_file_path)

    if not errors:
        return file_contents

    if raise_file_contents_on_error:
        raise ValidationError(f"Errors with generation: {errors}", file_contents)

    raise ValidationError(f"Errors with generation: {errors}")


TEMP_DIR = os.path.abspath("./../static_code_analysis")
DEFAULT_DEPS = ["prisma", "pyright", "pydantic"]


def setup_if_required():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)

    if os.path.exists(f"{TEMP_DIR}/venv"):
        return

    # Create a virtual environment
    output = execute_command(["python", "-m", "vvenv", "venv"], python_path=None)
    print(output)
    # Install dependencies
    output = execute_command(["pip", "install"] + DEFAULT_DEPS)
    print(output)


def execute_command(
    command: list[str],
    cwd=TEMP_DIR,
    python_path: str | None = f"{TEMP_DIR}/venv/bin",
    raise_on_error: bool = True,
) -> str:
    """
    Execute a command in the shell
    Args:
        command (list[str]): The command to execute
        cwd (str): The current working directory
        python_path (str): The python executable path
    Returns:
        str: The output of the command
    """
    try:
        # Set the python path by replacing the env 'PATH' with the python path
        venv = os.environ.copy()
        if python_path:
            original_python_path = venv["PATH"].split(":")[1:]
            venv["PATH"] = f"{python_path}:{':'.join(original_python_path)}"
        r = subprocess.run(
            command, cwd=cwd, shell=False, env=venv, capture_output=True, check=True
        )
        return (r.stdout or r.stderr or b"").decode("utf-8")
    except subprocess.CalledProcessError as e:
        if raise_on_error:
            raise ValidationError((e.stdout or e.stderr).decode("utf-8")) from e
        else:
            return e.output.decode("utf-8")
