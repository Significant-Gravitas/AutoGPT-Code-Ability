from typing import Callable

import prisma.enums
import prisma.models
import pytest
from dotenv import load_dotenv

import codex.common.test_const
from codex.api_model import ApplicationCreate, Identifiers
from codex.app import db_client
from codex.common import ai_block
from codex.common.ai_block import LLMFailure
from codex.common.ai_model import OpenAIChatClient
from codex.common.constants import TODO_COMMENT
from codex.common.logging_config import setup_logging
from codex.common.model import ObjectFieldModel, ObjectTypeModel
from codex.database import create_app
from codex.develop import agent
from codex.develop.database import get_compiled_code
from codex.interview.database import create_interview, create_interview_steps
from codex.interview.model import AppFeature, UnderstandRequest
from codex.requirements.agent import APIRouteSpec, Module, SpecHolder
from codex.requirements.database import create_specification
from codex.requirements.model import (
    DatabaseEnums,
    DatabaseSchema,
    DatabaseTable,
    DBResponse,
    PreAnswer,
)

load_dotenv()
is_connected = False
setup_logging()


async def create_sample_app(user_id: str, cloud_id: str):
    name = "TicTacToe Game"
    description = "Two Players TicTacToe Game communicate through an API."
    app_response = await create_app(
        user_id,
        ApplicationCreate(
            name=name,
            description=description,
        ),
    )

    app = await prisma.models.Application.prisma().find_first_or_raise(
        where={"id": app_response.id, "userId": user_id}
    )

    ids = Identifiers(user_id=user_id, app_id=app.id, cloud_services_id=cloud_id)

    interview = await create_interview(
        ids=ids,
        name="TicTacToe Game",
        description="Two Players TicTacToe Game communicate through an API.",
    )
    ids.interview_id = interview.id

    interview_step = await create_interview_steps(
        ids=ids,
        ans=UnderstandRequest(
            thoughts="The user wants to create a TicTacToe game where two players can play against each other. The game should be played through an API.",
            features=[
                AppFeature(
                    name="TicTacToe Game",
                    reasoning="Two Players TicTacToe Game communicate through an API.",
                    functionality="Two Players TicTacToe Game communicate through an API.",
                )
            ],
            say_to_user="I understand that you want to create a TicTacToe game where two players can play against each other. The game should be played through an API.",
            phase_completed=True,
        ),
    )

    spec = await create_specification(
        SpecHolder(
            ids=ids,
            app=app,
            features=[feature for feature in interview_step.Features or []],
            modules=[
                Module(
                    name="TicTacToe Game",
                    description="Two Players TicTacToe Game communicate through an API.",
                    api_routes=[
                        APIRouteSpec(
                            module_name="TicTacToe Game",
                            http_verb=prisma.enums.HTTPVerb.POST,
                            function_name="make_turn",
                            path="/make-turn",
                            description="Processes a player's move in the Tic-Tac-Toe game and returns the current state of the game.",
                            access_level=prisma.enums.AccessLevel.PUBLIC,
                            allowed_access_roles=[],
                            request_model=ObjectTypeModel(
                                name="MakeTurnRequest",
                                Fields=[
                                    ObjectFieldModel(name="game_id", type="str"),
                                    ObjectFieldModel(name="row", type="int"),
                                    ObjectFieldModel(name="col", type="int"),
                                ],
                            ),
                            response_model=ObjectTypeModel(
                                name="GameStateResponse",
                                Fields=[
                                    ObjectFieldModel(name="gameId", type="str"),
                                    ObjectFieldModel(name="turn", type="str"),
                                    ObjectFieldModel(name="state", type="str"),
                                    ObjectFieldModel(name="board", type="str"),
                                ],
                            ),
                        )
                    ],
                )
            ],
            db_response=DBResponse(
                think="I need to store the game state and board in a database.",
                anti_think="I don't need to store things like authentication tokens as this is a simple game.",
                plan="I will create a table to store the game state and board.",
                refine="I will create a table with columns for the game ID, turn, state, and board.",
                pre_answer=PreAnswer(tables=[{}], enums=[{}]),
                pre_answer_issues="I need to make sure the tables use the correct data types.",
                full_schema="""
                model Game {
                    id String @id @default(uuid())
                    gameId String
                    turn Turn
                    state GameState
                    board String
                }

                enum GameState {
                    Win
                    Loss
                    Draw
                    InProgress
                }

                enum Turn {
                    X
                    O
                }
                """,
                database_schema=DatabaseSchema(
                    name="TicTacToe DB",
                    description="Database for TicTacToe Game",
                    tables=[
                        DatabaseTable(
                            name="Game",
                            description="Game state and board",
                            definition="""
                            model Game {
                                id String @id @default(uuid())
                                gameId String
                                turn Turn
                                state GameState
                                board String
                            }
                            """,
                        )
                    ],
                    enums=[
                        DatabaseEnums(
                            name="GameState",
                            description="The current state of the game.",
                            values=["Win", "Loss", "Draw", "In Progress"],
                            definition="""
                            enum GameState {
                                Win
                                Loss
                                Draw
                                InProgress
                            }
                            """,
                        ),
                        DatabaseEnums(
                            name="Turn",
                            description="The current turn of the game.",
                            values=["X", "O"],
                            definition="""
                            enum Turn {
                                X
                                O
                            }
                            """,
                        ),
                    ],
                ),
                conclusions="I have created a table to store the game state and board.",
            ),
        )
    )

    return app.id, spec


async def with_db_connection(func: Callable):
    global is_connected
    if not is_connected:
        await db_client.connect()
        is_connected = True

    result = await func()

    if is_connected:
        await db_client.disconnect()
        is_connected = False

    return result


async def generate_function(
    user_id=codex.common.test_const.identifier_1.user_id,
    cloud_id="",
) -> list[str] | None:
    if not OpenAIChatClient._configured:
        OpenAIChatClient.configure({})

    async def execute():
        app_id, spec = await create_sample_app(user_id, cloud_id)  # type: ignore
        ids = codex.common.test_const.Identifiers(
            user_id=user_id, app_id=app_id, cloud_services_id=cloud_id
        )
        func = await agent.develop_application(ids=ids, spec=spec)
        return await get_compiled_code(func.id) if func else None

    return await with_db_connection(execute)


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
    assert "not implemented" in str(e.value)


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
    assert "Nested" in str(e.value)


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_with_llm_function_generation():
    ai_block.MOCK_RESPONSE = COMPLEX_RESPONSE
    func = await generate_function()
    assert func is not None


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_class_with_optional_field():
    ai_block.MOCK_RESPONSE = CLASS_WITH_OPTIONAL_FIELD_RESPONSE
    func = await generate_function()
    assert func is not None
    assert "class SomeClass" in func[0]
    assert "field1: Optional[int] = None" in func[0]


# TODO: continue this test when pyright is enabled.
@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_class_with_db_query():
    ai_block.MOCK_RESPONSE = DB_QUERY_RESPONSE
    func = await generate_function()
    assert func is not None
    assert "prisma.models.Game" in func[0]
    assert "prisma.enums.GameState" in func[0]
    assert "def get_game_state" in func[0]
    assert "def make_turn" in func[0]


@pytest.mark.asyncio
@pytest.mark.integration_test
async def test_with_undefined_entity():
    ai_block.MOCK_RESPONSE = UNDEFINED_ENTITY_RESPONSE
    result = await generate_function()
    assert result is not None
    assert TODO_COMMENT in result[0]
    assert "Undefined name `UnknownEntity`" in result[0]


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
    return GameStateResponse(board="X", gameId="1", state="InProgress", turn="X")
```
"""


WITH_GLOBAL_RESPONSE = """
```python
global_here = 1

def dependency_function():
    return

def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return GameStateResponse(board="X", gameId="1", state="InProgress", turn="X")
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
    return GameStateResponse(board="X", gameId="1", state="InProgress", turn="X")
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
    return GameStateResponse(board="X", gameId="1", state="InProgress", turn="X")
```
"""

CLASS_WITH_OPTIONAL_FIELD_RESPONSE = """
```python
class SomeClass:
    field1: int | None # Optional field should be prefilled with None default value.
    field2: Optional[Dict[str, int]] # Optional & Dict without import should work.

    def get_state(self) -> GameStateResponse:
        return GameStateResponse(board="X", gameId="1", state="InProgress", turn="X")

def some_method(input: SomeClass) -> GameStateResponse:
    return input.get_state()

def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return some_method(SomeClass())
```
"""

DB_QUERY_RESPONSE = """
```python
def get_game_state(game_id: str) -> GameStateResponse:
    game = await Game.prisma().find_first(where={"id": game_id, "gameState": str(GameState.InProgress)})
    return GameStateResponse(gameId=game.id, turn=game.turn, state=game.state, board=game.board)


def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return await get_game_state(game_id)
```
"""

UNDEFINED_ENTITY_RESPONSE = """
```python
def make_turn(game_id: str, row: int, col: int) -> GameStateResponse:
    return UnknownEntity.get_game_state(game_id)
```
"""
