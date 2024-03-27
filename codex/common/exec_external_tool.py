import asyncio
import enum
import logging
import os
import subprocess
import tempfile
from asyncio.subprocess import Process

from codex.common.ai_block import ValidationError

logger = logging.getLogger(__name__)


class OutputType(enum.Enum):
    STD_OUT = "stdout"
    STD_ERR = "stderr"
    BOTH = "both"


async def exec_external_on_contents(
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
            r: Process = await asyncio.create_subprocess_exec(
                *command_arguments,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = await r.communicate()
            stdout, stderr = result[0].decode("utf-8"), result[1].decode("utf-8")
            logger.debug(f"Output: {stdout}")
            if temp_file_path in stdout:
                stdout = stdout  # .replace(temp_file.name, "/generated_file")
                logger.debug(f"Errors: {stderr}")
                if output_type == OutputType.STD_OUT:
                    errors = stdout
                elif output_type == OutputType.STD_ERR:
                    errors = stderr
                else:
                    errors = stdout + "\n" + stderr

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


PROJECT_TEMP_DIR = os.path.join(tempfile.gettempdir(), "codex-static-code-analysis")
DEFAULT_DEPS = ["prisma", "pyright", "pydantic", "virtualenv-clone"]


async def setup_if_required(cwd: str, copy_from_parent: bool = False) -> str:
    """
    Setup the virtual environment if it does not exist
    This setup is executed expectedly once per application run
    Args:
        cwd (str): The current working directory
        copy_from_parent (bool): Whether to copy the virtual environment from the parent directory
    Returns:
        str: The path to the virtual environment
    """
    if not os.path.exists(cwd):
        os.makedirs(cwd, exist_ok=True)

    path = f"{cwd}/venv/bin"
    if os.path.exists(path):
        return path

    parent_dir = os.path.abspath(f"{cwd}/../")
    if copy_from_parent and os.path.exists(f"{parent_dir}/venv"):
        parent_path = await setup_if_required(parent_dir)
        await execute_command(
            ["virtualenv-clone", f"{parent_dir}/venv", f"{cwd}/venv"], cwd, parent_path
        )
        return path

    # Create a virtual environment
    output = await execute_command(["python", "-m", "venv", "venv"], cwd, None)
    logger.debug(output)

    # Install dependencies
    output = await execute_command(["pip", "install"] + DEFAULT_DEPS, cwd, path)
    logger.debug(output)

    return path


async def execute_command(
    command: list[str],
    cwd: str | None,
    python_path: str | None,
    raise_on_error: bool = True,
) -> str:
    """
    Execute a command in the shell
    Args:
        command (list[str]): The command to execute
        cwd (str): The current working directory
        python_path (str): The python executable path
        raise_on_error (bool): Whether to raise an error if the command fails
    Returns:
        str: The output of the command
    """
    try:
        # Set the python path by replacing the env 'PATH' with the provided python path
        venv = os.environ.copy()
        if python_path:
            # PATH prioritize first occurrence of python_path, so we need to prepend.
            venv["PATH"] = python_path + ":" + venv["PATH"]
        r = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=venv,
        )
        stdout, stderr = await r.communicate()
        return (stdout or stderr).decode("utf-8")
    except subprocess.CalledProcessError as e:
        if raise_on_error:
            raise ValidationError((e.stderr or e.stdout).decode("utf-8")) from e
        else:
            return e.output.decode("utf-8")
