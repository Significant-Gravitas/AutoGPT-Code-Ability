import logging
import os
import subprocess
import tempfile

from codex.common.ai_block import ValidationError

logger = logging.getLogger(__name__)


def exec_external_on_contents(
    command_arguments: list[str], file_contents, suffix: str = ".py"
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
            logger.info(f"Output: {result.stdout}")
            if temp_file_path in result.stdout:
                stderr = result.stdout.replace(temp_file.name, "generated_file")
                logger.error(f"Errors: {stderr}")
                errors = stderr
            with open(temp_file_path, "r") as f:
                file_contents = f.read()
        finally:
            # Ensure the temporary file is deleted
            os.remove(temp_file_path)

    if errors:
        raise ValidationError(f"Errors with code generation: {errors}")

    return file_contents