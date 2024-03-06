import pytest
from dotenv import load_dotenv

from codex.app import db_client
from codex.common import ai_block
from codex.common.ai_block import LLMFailure
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.test_const import Identifiers, app_id_11, user_id_1
from codex.develop import agent
from codex.requirements.database import get_latest_specification

load_dotenv()


OpenAIChatClient.configure({})
setup_logging(local=True)

is_connected = False


async def generate_function():
    global is_connected

    if not is_connected:
        await db_client.connect()
        is_connected = True

    ids = Identifiers(user_id=user_id_1, app_id=app_id_11, cloud_services_id="")
    spec = await get_latest_specification(ids.user_id, ids.app_id)
    func = await agent.develop_application(ids=ids, spec=spec)

    if is_connected:
        await db_client.disconnect()
        is_connected = False

    return func


@pytest.mark.asyncio
async def test_simple_function():
    ai_block.MOCK_RESPONSE = SIMPLE_RESPONSE
    func = await generate_function()
    assert func is not None


@pytest.mark.asyncio
async def test_global_variable():
    ai_block.MOCK_RESPONSE = WITH_GLOBAL_RESPONSE
    result = await generate_function()
    assert result is not None


@pytest.mark.asyncio
async def test_unimplemented_function():
    ai_block.MOCK_RESPONSE = WITH_UNIMPLEMENTED_FUNCTION_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "unimplemented" in str(e.value)


@pytest.mark.asyncio
async def test_mismatching_arguments():
    ai_block.MOCK_RESPONSE = WITH_MISMATCHING_ARGUMENTS_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "arguments" in str(e.value)


@pytest.mark.asyncio
async def test_mismatching_return_type():
    ai_block.MOCK_RESPONSE = WITH_MISMATCHING_RETURN_TYPE_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "return type" in str(e.value)


@pytest.mark.asyncio
async def test_nested_function():
    ai_block.MOCK_RESPONSE = WITH_NESTED_FUNCTION_RESPONSE
    with pytest.raises(LLMFailure) as e:
        await generate_function()
        assert "nested" in str(e.value)


@pytest.mark.asyncio
async def test_with_llm_function_generation():
    ai_block.MOCK_RESPONSE = COMPLEX_RESPONSE
    func = await generate_function()
    assert func is not None


COMPLEX_RESPONSE = """
```requirements
pydantic==1.9.0
```

```python
from typing import Dict, List
from pydantic import BaseModel

class TurnRequest(BaseModel):
    \"\"\"
    A request model for making a move in a Tic-Tac-Toe game, using Pydantic for data validation.

    Args:
        row (int): The row in which the move is made, value should be between 1 and 3 inclusively.
        column (int): The column in which the move is made, value should be between 1 and 3 inclusively.
    \"\"\"
    row: int
    column: int

class GameStateResponse(BaseModel):
    \"\"\"
    A response model containing the current state of the Tic-Tac-Toe game, using Pydantic for data validation.

    Args:
        gameId (str): The unique identifier of the game.
        turn (str): The current turn of the game, could be 'X' or 'O'.
        state (str): The current state of the game, could be 'In Progress', 'Draw', 'Win', or 'Loss'.
        board (str): A string representation of the current game board.
    \"\"\"
    gameId: str
    turn: str
    state: str
    board: str

current_game: Dict[str, str] = {'gameId': '1', 'turn': 'X', 'state': 'In Progress', 'board': [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']}

def check_win_or_draw(board: list) -> str:
    \"\"\"
    Determines the current state of the Tic-Tac-Toe game board, whether it's a win, draw, or still in progress.

    Args:
        board (list): The current state of the game board as a list of 9 strings.

    Returns:
        str: The game status, being either 'Win', 'Loss', 'Draw', or 'In Progress'.
    \"\"\"
    win_conditions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Horizontal
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Vertical
        (0, 4, 8), (2, 4, 6)  # Diagonal
    ]

    for condition in win_conditions:
        if board[condition[0]] == board[condition[1]] == board[condition[2]] != ' ':
            return 'Win' if current_game['turn'] == 'X' else 'Loss'

    if ' ' not in board:
        return 'Draw'

    return 'In Progress'

def make_turn(request: TurnRequest) -> GameStateResponse:
    \"\"\"
    Processes a player's move in the Tic-Tac-Toe game and returns the current state of the game.

    Args:
        request (TurnRequest): Contains the details of the player's move (row and column).

    Returns:
        GameStateResponse: The current state of the game after processing the move.
    \"\"\"
    global current_game  # Necessary for modifying the global variable

    if not current_game['state'] == 'In Progress':
        # Resetting the game if not in progress
        current_game['board'] = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        current_game['state'] = 'In Progress'

    index = (request.row - 1) * 3 + (request.column - 1)
    if current_game['board'][index] == ' ':
        current_game['board'][index] = current_game['turn']

        # Check the game state after the move
        current_game['state'] = check_win_or_draw(current_game['board'])

        # Switch turns
        current_game['turn'] = 'O' if current_game['turn'] == 'X' else 'X'

    board_str = '\\n'.join([' '.join(current_game['board'][i:i+3]) for i in range(0, 9, 3)])

    return GameStateResponse(**current_game, board=board_str)
```
"""


WITH_NESTED_FUNCTION_RESPONSE = """
```python
def make_turn(request: TurnRequest) -> GameStateResponse:
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

def make_turn(request: TurnRequest) -> GameStateResponse:
    return GameStateResponse()
```
"""

WITH_UNIMPLEMENTED_FUNCTION_RESPONSE = """
```python
def make_turn(request: TurnRequest) -> GameStateResponse:
    pass
```
"""

WITH_MISMATCHING_ARGUMENTS_RESPONSE = """
```python
def make_turn(turn: int, request: TurnRequest) -> GameStateResponse:
    return GameStateResponse()
```
"""

WITH_MISMATCHING_RETURN_TYPE_RESPONSE = """
```python
def make_turn(request: TurnRequest) -> int:
    return 1
```
"""

SIMPLE_RESPONSE = """
```python
def make_turn(request: TurnRequest) -> GameStateResponse:
    return GameStateResponse()
```
"""
