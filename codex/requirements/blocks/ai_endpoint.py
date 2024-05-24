import logging
import typing
from typing import Any, Dict, List, Optional, Set, Tuple

from codex.api_model import ObjectFieldModel, ObjectTypeModel
from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.requirements.model import EndpointSchemaRefinementResponse

logger = logging.getLogger(__name__)


def extract_types(
    obj: Any, types: Set[str], object_types: List[ObjectTypeModel]
) -> None:
    if isinstance(obj, ObjectTypeModel):
        types.add(obj.name)
        object_types.append(obj)
        if obj.Fields:
            for field in obj.Fields:
                extract_types(field, types, object_types)
    elif isinstance(obj, ObjectFieldModel):
        extract_field_types(obj.type, types)
        if obj.related_types:
            for related_type in obj.related_types:
                extract_types(related_type, types, object_types)
    elif isinstance(obj, list):
        for item in obj:
            extract_types(item, types, object_types)


def extract_field_types(field_type: str, types: Set[str]) -> None:
    field_type = field_type.replace(" ", "")
    if "[" in field_type:
        outer_type, inner_type = extract_outer_inner_types(field_type)
        types.add(outer_type)
        replaced_inner_types = replace_inner_types(inner_type)
        for inner_type_part in replaced_inner_types:
            extract_field_types(inner_type_part, types)
    else:
        types.add(field_type)


ALLOWED_TYPES = sorted(typing.__all__) + [
    "int",
    "float",
    "str",
    "bool",
    "bytes",
    "bytearray",
    "complex",
    "dict",
    "frozenset",
    "list",
    "set",
    "tuple",
    "range",
    "slice",
    "memoryview",
    "None",
    "NotImplemented",
    "Ellipsis",
    "type",
    "object",
    "property",
    "classmethod",
    "staticmethod",
    "super",
    "datetime",
    "date",
    "time",
    "timedelta",
    "timezone",
    "enum",
    "array",
    "deque",
    "defaultdict",
    "OrderedDict",
    "Counter",
    "ChainMap",
    "namedtuple",
    "Path",
    "PosixPath",
    "WindowsPath",
    "UploadFile",
]


def is_valid_type(
    type_name: str,
    object_type_names: Set[str],
    allowed_types: List[str],
) -> bool:
    return type_name in object_type_names or type_name in allowed_types


def replace_types(types: Set[str]) -> Set[str]:
    type_replacements = {
        "any": "Any",
        "list": "List",
        "dict": "Dict",
        "tuple": "Tuple",
        "set": "Set",
        "optional": "Optional",
        "union": "Union",
        "callable": "Callable",
        "iterable": "Iterable",
        "iterator": "Iterator",
        "generator": "Generator",
        "sequence": "Sequence",
        "mapping": "Mapping",
        "mutablemapping": "MutableMapping",
        "hashable": "Hashable",
        "typevar": "TypeVar",
        "generic": "Generic",
        "type": "Type",
        "bytestring": "ByteString",
        "anystr": "AnyStr",
        "text": "Text",
        "io": "IO",
        "binaryio": "BinaryIO",
        "textio": "TextIO",
        "contextmanager": "ContextManager",
        "asynciterable": "AsyncIterable",
        "asynciterator": "AsyncIterator",
        "asyncgenerator": "AsyncGenerator",
        "coroutine": "Coroutine",
        "collection": "Collection",
        "abstractset": "AbstractSet",
        "mutableset": "MutableSet",
        "mutablesequence": "MutableSequence",
        "counter": "Counter",
        "deque": "Deque",
        "defaultdict": "DefaultDict",
        "ordereddict": "OrderedDict",
        "chainmap": "ChainMap",
        "awaitable": "Awaitable",
        "asynccontextmanager": "AsyncContextManager",
        "newtype": "NewType",
        "namedtuple": "NamedTuple",
        "protocol": "Protocol",
        "final": "Final",
        "literal": "Literal",
        "classvar": "ClassVar",
        "annotated": "Annotated",
        "typeddict": "TypedDict",
        "supportsint": "SupportsInt",
        "supportsfloat": "SupportsFloat",
        "supportscomplex": "SupportsComplex",
        "supportsbytes": "SupportsBytes",
        "supportsabs": "SupportsAbs",
        "supportsround": "SupportsRound",
        "reversible": "Reversible",
        "container": "Container",
    }

    return {type_replacements.get(type_name.lower(), type_name) for type_name in types}


def replace_object_model_types(obj: Any) -> None:
    if isinstance(obj, ObjectTypeModel):
        if obj.Fields:
            for field in obj.Fields:
                replace_object_model_types(field)
    elif isinstance(obj, ObjectFieldModel):
        obj.type = replace_field_type(obj.type)
        if obj.related_types:
            for related_type in obj.related_types:
                replace_object_model_types(related_type)
    elif isinstance(obj, list):
        for item in obj:
            replace_object_model_types(item)


def replace_field_type(field_type: str) -> str:
    type_replacements = {
        "any": "Any",
        "list": "List",
        "dict": "Dict",
        "tuple": "Tuple",
        "set": "Set",
        "optional": "Optional",
        "union": "Union",
        "callable": "Callable",
        "iterable": "Iterable",
        "iterator": "Iterator",
        "generator": "Generator",
        "sequence": "Sequence",
        "mapping": "Mapping",
        "mutablemapping": "MutableMapping",
        "hashable": "Hashable",
        "typevar": "TypeVar",
        "generic": "Generic",
        "type": "Type",
        "bytestring": "ByteString",
        "anystr": "AnyStr",
        "text": "Text",
        "io": "IO",
        "binaryio": "BinaryIO",
        "textio": "TextIO",
        "contextmanager": "ContextManager",
        "asynciterable": "AsyncIterable",
        "asynciterator": "AsyncIterator",
        "asyncgenerator": "AsyncGenerator",
        "coroutine": "Coroutine",
        "collection": "Collection",
        "abstractset": "AbstractSet",
        "mutableset": "MutableSet",
        "mutablesequence": "MutableSequence",
        "counter": "Counter",
        "deque": "Deque",
        "defaultdict": "DefaultDict",
        "ordereddict": "OrderedDict",
        "chainmap": "ChainMap",
        "awaitable": "Awaitable",
        "asynccontextmanager": "AsyncContextManager",
        "newtype": "NewType",
        "namedtuple": "NamedTuple",
        "protocol": "Protocol",
        "final": "Final",
        "literal": "Literal",
        "classvar": "ClassVar",
        "annotated": "Annotated",
        "typeddict": "TypedDict",
        "supportsint": "SupportsInt",
        "supportsfloat": "SupportsFloat",
        "supportscomplex": "SupportsComplex",
        "supportsbytes": "SupportsBytes",
        "supportsabs": "SupportsAbs",
        "supportsround": "SupportsRound",
        "reversible": "Reversible",
        "container": "Container",
    }

    field_type = field_type.replace(" ", "")
    if "[" in field_type:
        outer_type, inner_type = extract_outer_inner_types(field_type)
        outer_type = type_replacements.get(outer_type.lower(), outer_type)
        replaced_inner_types = replace_inner_types(inner_type)
        return f"{outer_type}[{', '.join(replaced_inner_types)}]"
    else:
        return type_replacements.get(field_type.lower(), field_type)


def extract_outer_inner_types(field_type: str) -> Tuple[str, str]:
    bracket_count = 0
    outer_type = ""
    inner_type = ""
    for char in field_type:
        if char == "[":
            bracket_count += 1
            if bracket_count == 1:
                continue
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0:
                break
        if bracket_count == 0:
            outer_type += char
        else:
            inner_type += char
    return outer_type, inner_type


def replace_inner_types(inner_type: str) -> List[str]:
    replaced_inner_types = []
    bracket_count = 0
    current_type = ""
    for char in inner_type:
        if char == "[":
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
        elif char == "," and bracket_count == 0:
            replaced_inner_types.append(replace_field_type(current_type))
            current_type = ""
            continue
        current_type += char
    if current_type:
        replaced_inner_types.append(replace_field_type(current_type))
    return replaced_inner_types


def copy_object_type(
    source_model: ObjectTypeModel, target_model: ObjectTypeModel, object_type_name: str
) -> bool:
    def find_object_type(fields: List[Any]) -> Optional[ObjectTypeModel]:
        for field in fields:
            if isinstance(field, ObjectTypeModel) and field.name == object_type_name:
                return field
            elif isinstance(field, ObjectFieldModel) and field.related_types:
                found_type = find_object_type(field.related_types)
                if found_type:
                    return found_type
        return None

    logging.debug(f"Searching for object type: {object_type_name}")
    found_type = find_object_type(source_model.Fields or [])
    if found_type:
        logging.debug(f"Copying object type: {object_type_name}")
        copied_object_type = found_type.copy(deep=True)

        # Find the fields in the target model that reference the object type
        if target_model.Fields:
            for field in target_model.Fields:
                if (
                    isinstance(field, ObjectFieldModel)
                    and object_type_name in field.type
                ):
                    if not field.related_types:
                        field.related_types = []
                    field.related_types.append(copied_object_type)
        return True
    else:
        logging.debug(f"Object type not found: {object_type_name}")
        return False


def resolve_invalid_types(
    invalid_types: List[str],
    source_model: ObjectTypeModel,
    target_model: ObjectTypeModel,
) -> List[str]:
    resolved_types: List[str] = []
    for invalid_type in invalid_types:
        logging.warn(f"Resolving invalid type: {invalid_type}")
        if copy_object_type(source_model, target_model, invalid_type):
            resolved_types.append(invalid_type)
    return resolved_types


def attach_related_types(
    model: ObjectTypeModel, defined_types: Dict[str, ObjectTypeModel]
) -> None:
    if model.Fields:
        for field in model.Fields:
            types = set()
            extract_field_types(field.type, types)
            for type_name in types:
                if type_name in defined_types:
                    if defined_types[type_name] not in (field.related_types or []):
                        if not field.related_types:
                            field.related_types = []
                        field.related_types.append(defined_types[type_name])
                else:
                    if field.related_types:
                        for related_type in field.related_types:
                            if related_type.name == type_name:
                                defined_types[type_name] = related_type
                                break
            if field.related_types:
                for related_type in field.related_types:
                    attach_related_types(related_type, defined_types)
    # Check for all the models if they don't have related types attached
    for field in model.Fields or []:
        types = set()
        extract_field_types(field.type, types)
        for type_name in types:
            if type_name in defined_types:
                for other_model in defined_types.values():
                    if other_model.name == type_name:
                        if not field.related_types:
                            field.related_types = []
                        if other_model not in field.related_types:
                            field.related_types.append(other_model)
                        break
    defined_types[model.name] = model


def parse_object_model(
    request_model: ObjectTypeModel,
    response_model: ObjectTypeModel,
    allowed_types: List[str],
) -> Tuple[
    Set[str],
    Set[str],
    List[ObjectTypeModel],
    List[ObjectTypeModel],
    ObjectTypeModel,
    ObjectTypeModel,
    List[str],
    List[str],
]:
    request_types: Set[str] = set()
    response_types: Set[str] = set()
    request_object_types: List[ObjectTypeModel] = []
    response_object_types: List[ObjectTypeModel] = []

    extract_types(request_model, request_types, request_object_types)
    extract_types(response_model, response_types, response_object_types)

    request_types = replace_types(request_types)
    response_types = replace_types(response_types)

    replace_object_model_types(request_model)
    replace_object_model_types(response_model)

    request_type_names = {obj_type.name for obj_type in request_object_types}
    response_type_names = {obj_type.name for obj_type in response_object_types}

    invalid_request_types = [
        type_name
        for type_name in request_types
        if not is_valid_type(type_name, request_type_names, allowed_types)
    ]
    invalid_response_types = [
        type_name
        for type_name in response_types
        if not is_valid_type(type_name, response_type_names, allowed_types)
    ]

    while invalid_request_types or invalid_response_types:
        resolved_request_types = resolve_invalid_types(
            invalid_request_types, response_model, request_model
        )
        resolved_response_types = resolve_invalid_types(
            invalid_response_types, request_model, response_model
        )

        if not resolved_request_types and not resolved_response_types:
            break

        invalid_request_types = [
            type_name
            for type_name in invalid_request_types
            if type_name not in resolved_request_types
        ]
        invalid_response_types = [
            type_name
            for type_name in invalid_response_types
            if type_name not in resolved_response_types
        ]

    request_defined_types: Dict[str, ObjectTypeModel] = {}
    response_defined_types: Dict[str, ObjectTypeModel] = {}
    attach_related_types(request_model, request_defined_types)
    attach_related_types(response_model, response_defined_types)

    request_types_post: Set[str] = set()
    response_types_post: Set[str] = set()
    request_object_types_post: List[ObjectTypeModel] = []
    response_object_types_post: List[ObjectTypeModel] = []

    extract_types(request_model, request_types_post, request_object_types_post)
    extract_types(response_model, response_types_post, response_object_types_post)

    request_type_names_post = {obj_type.name for obj_type in request_object_types_post}
    response_type_names_post = {
        obj_type.name for obj_type in response_object_types_post
    }

    invalid_request_types_post = [
        type_name
        for type_name in request_types_post
        if not is_valid_type(type_name, request_type_names_post, allowed_types)
    ]
    invalid_response_types_post = [
        type_name
        for type_name in response_types_post
        if not is_valid_type(type_name, response_type_names_post, allowed_types)
    ]

    return (
        request_types_post,
        response_types_post,
        request_object_types_post,
        response_object_types_post,
        request_model,
        response_model,
        invalid_request_types_post,
        invalid_response_types_post,
    )


class EndpointSchemaRefinementBlock(AIBlock):
    """
    This is a block that handles, calling the LLM, validating the response,
    storing llm calls, and returning the response to the user

    """

    # The name of the prompt template folder in codex/prompts/{model}
    prompt_template_name = "requirements/endpoint"
    # Model to use for the LLM
    model = "gpt-4o"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = EndpointSchemaRefinementResponse

    async def validate(
        self, invoke_params: dict, response: ValidatedResponse
    ) -> ValidatedResponse:
        """
        The validation logic for the response. In this case its really simple as we
        are just validating the response is a Clarification model. However, in the other
        blocks this is much more complex. If validation failes it triggers a retry.
        """
        try:
            model: EndpointSchemaRefinementResponse = (
                EndpointSchemaRefinementResponse.model_validate_json(
                    response.response, strict=False
                )
            )
            # Perform additional validation
            # 0. check that all the ObjectTypes are valid python using the pydantic model and only typing
            # 1. Check that all the ObjectTypes have definitions or a matching enum or table in the database schema
            # 2. Check that all the fields in the ObjectType have definitions or a matching field in the database schema
            # 3. Check that all the fields in the ObjectType have a correct type

            (
                request_types,
                response_types,
                request_object_types,
                response_object_types,
                new_request_model,
                new_response_model,
                invalid_request_types,
                invalid_response_types,
            ) = parse_object_model(
                request_model=model.api_endpoint.request_model,
                response_model=model.api_endpoint.response_model,
                allowed_types=invoke_params["allowed_types"],
            )

            error_message = ""
            if invalid_request_types:
                error_message += f"Invalid types in request: {invalid_request_types}\n"
            if invalid_response_types:
                error_message += (
                    f"Invalid types in response: {invalid_response_types}\n"
                )

            if error_message:
                raise ValidationError(
                    error_message + f"Allowed types: {invoke_params['allowed_types']}"
                )

            model.api_endpoint.request_model = new_request_model
            model.api_endpoint.response_model = new_response_model

            response.response = model
        except Exception as e:
            raise ValidationError(f"Error validating response: {e}")

        return response

    async def create_item(
        self, ids: Identifiers, validated_response: ValidatedResponse
    ):
        """
        This is where we would store the response in the database

        Atm I don't have a database model to store QnA responses, but we can add one
        """
        pass
