import pytest
from dotenv import load_dotenv

from codex.app import db_client
from codex.common import ai_block
from codex.common.ai_block import LLMFailure
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.test_const import Identifiers, app_id_11, user_id_1
from codex.develop import agent
from codex.requirements.database import get_latest_specification, get_specification

load_dotenv()
if not OpenAIChatClient._configured:
    OpenAIChatClient.configure({})
setup_logging(local=True)

is_connected = False


async def generate_function(
    user_id=user_id_1,
    app_id=app_id_11,
    cloud_id="",
    spec_id="",
):
    global is_connected

    if not is_connected:
        await db_client.connect()
        is_connected = True

    ids = Identifiers(user_id=user_id, app_id=app_id, cloud_services_id=cloud_id)
    if spec_id != "":
        spec = await get_specification(ids.user_id, ids.app_id, spec_id)
    else:
        spec = await get_latest_specification(ids.user_id, ids.app_id)
    func = await agent.develop_application(ids=ids, spec=spec)

    if is_connected:
        await db_client.disconnect()
        is_connected = False

    return func


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_simple_function():
    ai_block.MOCK_RESPONSE = SIMPLE_RESPONSE
    func = await generate_function()
    assert func is not None


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_global_variable():
    ai_block.MOCK_RESPONSE = WITH_GLOBAL_RESPONSE
    result = await generate_function()
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_unimplemented_function():
    ai_block.MOCK_RESPONSE = WITH_UNIMPLEMENTED_FUNCTION_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "unimplemented" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_mismatching_arguments():
    ai_block.MOCK_RESPONSE = WITH_MISMATCHING_ARGUMENTS_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "arguments" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_mismatching_return_type():
    ai_block.MOCK_RESPONSE = WITH_MISMATCHING_RETURN_TYPE_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "return type" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_nested_function():
    ai_block.MOCK_RESPONSE = WITH_NESTED_FUNCTION_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "nested" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_with_llm_function_generation():
    # ai_block.MOCK_RESPONSE = COMPLEX_RESPONSE
    func = await generate_function()
    assert func is not None


COMPLEX_RESPONSE = """
```requirements
pydantic==1.9.0
```

```python
from typing import Any, Dict, List
from pydantic import BaseModel
    
class Board(BaseModel):
    size: int
    cells: List[str]
    
    def __init__(self, size: int):
        self.size = size
        self.cells = [' ' for _ in range(size ** 2)]

class SomeCustomClass(BaseModel):
    request: int
    response: GameStateResponse

def some_helper_function(custom_arg: SomeCustomClass) -> SomeCustomClass:
    return custom_arg

current_game: Dict[str, Any] = {'gameId': '1', 'turn': 'X', 'state': 'In Progress', 'board': Board(3)}

def check_win_or_draw(board: Board) -> str:
    \"\"\"
    Determines the current state of the Tic-Tac-Toe game board, whether it's a win, draw, or still in progress.

    Args:
        board (Board): The current game board.

    Returns:
        str: The game status, being either 'Win', 'Loss', 'Draw', or 'In Progress'.
    \"\"\"
    win_conditions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Horizontal
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Vertical
        (0, 4, 8), (2, 4, 6)  # Diagonal
    ]

    cells = board.cells
    for condition in win_conditions:
        if cells[condition[0]] == cells[condition[1]] == cells[condition[2]] != ' ':
            return 'Win' if current_game['turn'] == 'X' else 'Loss'

    if ' ' not in cells:
        return 'Draw'

    return 'In Progress'

def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    \"\"\"
    Processes a player's move in the Tic-Tac-Toe game and returns the current state of the game.

    Args:
        game_id (int): The unique identifier of the game.
        row (int): The row in which the move is made, value should be between 1 and 3 inclusively.
        col (int): The column in which the move is made, value should be between 1 and 3 inclusively.

    Returns:
        GameStateResponse: The current state of the game after processing the move.
    \"\"\"
    global current_game  # Necessary for modifying the global variable
    cells = current_game['board'].cells

    if not current_game['state'] == 'In Progress':
        # Resetting the game if not in progress
        cells = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        current_game['state'] = 'In Progress'

    index = (row - 1) * 3 + (col - 1)
    if cells[index] == ' ':
        cells[index] = current_game['turn']

        # Check the game state after the move
        current_game['state'] = check_win_or_draw(current_game['board'])

        # Switch turns
        current_game['turn'] = 'O' if current_game['turn'] == 'X' else 'X'

    board_str = '\\n'.join([' '.join(cells[i:i+3]) for i in range(0, 9, 3)])

    return GameStateResponse(**current_game, board=board_str)
```
"""


WITH_NESTED_FUNCTION_RESPONSE = """
```python
def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    def nested_function():
        pass
    return GameStateResponse()
```
"""


WITH_GLOBAL_RESPONSE = """
```python
global_here = 1

def dependency_function():
    return

def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return GameStateResponse()
```
"""

WITH_UNIMPLEMENTED_FUNCTION_RESPONSE = """
```python
def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    pass
```
"""

WITH_MISMATCHING_ARGUMENTS_RESPONSE = """
```python
def make_turn(turn: int, row: int, col: int) -> GameStateResponse:
    return GameStateResponse()
```
"""

WITH_MISMATCHING_RETURN_TYPE_RESPONSE = """
```python
def make_turn(game_id: str, row: int, col: int) -> int:
    return 1
```
"""

SIMPLE_RESPONSE = """
```python
def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return GameStateResponse()
```
"""
