from shutil import which

import pytest

from codex.common.exec_external_tool import OutputType, exec_external_on_contents


@pytest.mark.asyncio
async def test_exec_external():
    # Test case 1: Valid command arguments and file contents
    command_arguments = ["cat"]
    file_contents = "print('Hello World')"
    expected_output = "print('Hello World')"

    result = await exec_external_on_contents(command_arguments, file_contents)
    assert result == expected_output


@pytest.mark.asyncio
async def test_exec_external_no_command():
    # Test case 2: Empty command arguments
    command_arguments = []
    file_contents = "print('Hello World')"

    with pytest.raises(AssertionError):
        await exec_external_on_contents(command_arguments, file_contents)


@pytest.mark.asyncio
async def test_exec_external_invalid_command():
    # Test case 3: Command execution error
    command_arguments = ["invalid_command"]
    file_contents = "print('Hello World')"

    with pytest.raises(Exception):
        await exec_external_on_contents(command_arguments, file_contents)


# This test only runs if I'm in debug mode on vscode?????????????? otherwise it can't find
# the ruff command
@pytest.mark.asyncio
async def test_exec_external_with_ruff():
    if which("ruff") is None:
        pytest.skip("Ruff not installed")
    # Test case 4: Command execution with ruff
    command_arguments = ["ruff", "check"]
    file_contents = "print('Hello World')"
    expected_output = "print('Hello World')"

    result = await exec_external_on_contents(
        command_arguments, file_contents, output_type=OutputType.STD_OUT
    )
    assert result == expected_output


# This test only runs if I'm in debug mode on vscode?????????????? otherwise it can't find
# the ruff command
@pytest.mark.asyncio
async def test_exec_external_with_ruff_fails():
    if which("ruff") is None:
        pytest.skip("Ruff not installed")
    # Test case 5: Command execution with ruff fails
    command_arguments = ["ruff", "check"]
    file_contents = "print('Hello World'"
    with pytest.raises(Exception) as exc_info:
        await exec_external_on_contents(
            command_arguments, file_contents, output_type=OutputType.STD_OUT
        )
    assert exc_info.value.args[0]


## This test only runs if I'm in debug mode on vscode?????????????? otherwise it can't find
# the prisma command
@pytest.mark.asyncio
async def test_exec_external_with_prisma():
    if which("prisma") is None:
        pytest.skip("Prisma not installed")
    # Test case 6: Command execution with prisma
    command_arguments = ["prisma", "validate", "--schema"]
    file_contents = (
        "model User {\n  id Int @id @default(autoincrement())\n  name String\n}"
    )
    expected_output = (
        "model User {\n  id Int @id @default(autoincrement())\n  name String\n}"
    )

    result = await exec_external_on_contents(
        command_arguments, file_contents, output_type=OutputType.STD_ERR
    )
    assert result == expected_output
