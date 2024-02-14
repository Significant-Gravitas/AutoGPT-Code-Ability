from typing import Type, TypeVar
from gravitasml.token import tokenize, Token
from gravitasml.parser import Parser
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def parse(text: str):
    tokens = tokenize(text)
    parser = Parser(tokens)
    return parser.parse()


def parse_into_model(text: str, model: Type[T]) -> T | list[T]:
    tokens = tokenize(text)
    parser = Parser(tokens)
    return parser.parse_to_pydantic(model)  # type: ignore
