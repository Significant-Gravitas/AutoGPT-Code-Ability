import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from codex.common.ai_block import (
    AIBlock,
    Identifiers,
    ValidatedResponse,
    ValidationError,
)
from codex.common.logging_config import setup_logging
from codex.common.model import ObjectFieldModel, ObjectTypeModel
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


def is_valid_type(
    type_name: str,
    object_type_names: Set[str],
    enum_names: List[str],
    table_names: List[str],
) -> bool:
    typing_types = [
        "List",
        "Dict",
        "Tuple",
        "Set",
        "Any",
        "Optional",
        "Union",
        "Callable",
        "Iterable",
        "Iterator",
        "Generator",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "Hashable",
        "TypeVar",
        "Generic",
        "Type",
        "ByteString",
        "AnyStr",
        "Text",
        "IO",
        "BinaryIO",
        "TextIO",
        "ContextManager",
        "AsyncIterable",
        "AsyncIterator",
        "AsyncGenerator",
        "Coroutine",
        "Collection",
        "AbstractSet",
        "MutableSet",
        "Mapping",
        "MutableMapping",
        "Sequence",
        "MutableSequence",
        "Counter",
        "Deque",
        "DefaultDict",
        "OrderedDict",
        "ChainMap",
        "Awaitable",
        "AsyncIterable",
        "AsyncIterator",
        "AsyncContextManager",
        "NewType",
        "NamedTuple",
        "Protocol",
        "Final",
        "Literal",
        "ClassVar",
        "Annotated",
        "TypedDict",
        "SupportsInt",
        "SupportsFloat",
        "SupportsComplex",
        "SupportsBytes",
        "SupportsAbs",
        "SupportsRound",
        "Reversible",
        "Container",
        "DateTime",
        "Date",
        "Time",
        "Timedelta",
        "Timezone",
        "Enum",
        "IntEnum",
        "Flag",
        "IntFlag",
        "Path",
        "PosixPath",
        "WindowsPath",
        "Array",
    ]

    default_types = [
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
    ]
    return (
        type_name in object_type_names
        or type_name in typing_types
        or type_name in default_types
        or type_name in enum_names
        or type_name in table_names
    )


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
    enum_names: List[str],
    table_names: List[str],
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
        if not is_valid_type(type_name, request_type_names, enum_names, table_names)
    ]
    invalid_response_types = [
        type_name
        for type_name in response_types
        if not is_valid_type(type_name, response_type_names, enum_names, table_names)
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
        if not is_valid_type(
            type_name, request_type_names_post, enum_names, table_names
        )
    ]
    invalid_response_types_post = [
        type_name
        for type_name in response_types_post
        if not is_valid_type(
            type_name, response_type_names_post, enum_names, table_names
        )
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
    model = "gpt-4-0125-preview"
    # Should we force the LLM to reply in JSON
    is_json_response = True
    # If we are using is_json_response, what is the response model
    pydantic_object = EndpointSchemaRefinementResponse

    def validate(
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
                enum_names=invoke_params["db_enums"],
                table_names=invoke_params["db_models"],
            )

            if invalid_request_types or invalid_response_types:
                raise ValidationError(
                    f"Invalid types in request or response: {invalid_request_types} {invalid_response_types}"
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


if __name__ == "__main__":
    """
    This is a simple test to run the block
    """
    from asyncio import run

    from prisma import Prisma

    from codex.common.ai_model import OpenAIChatClient
    from codex.common.test_const import identifier_1

    ids = identifier_1

    setup_logging(local=True)

    OpenAIChatClient.configure({})
    db_client = Prisma(auto_register=True)
    logging.info("Running block")

    invoke_params = {
        "spec": '# Tutor App\n\n## Task \nThe Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.\n\n### Project Description\nThe Tutor App is an app designed for tutors to manage their clients,\n schedules, and invoices.\n\nIt must support both the client and tutor scheduling, rescheduling and canceling\n appointments, and sending invoices after the appointment has passed.\n\nClients can sign up with OAuth2 or with traditional sign-in authentication. If they sign\n up with traditional authentication, it must be safe and secure. There will need to be\n password reset and login capabilities.\n\nThere will need to be authorization for identifying clients vs the tutor.\n\nAdditionally, it will have proper management of financials, including invoice management\n and payment tracking. This includes things like paid/failed invoice notifications,\n unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports.\n\n### Product Description\nTutorMate is designed as the ultimate app for tutors and their clients, focusing on managing schedules, financials, and communication seamlessly. It supports scheduling, rescheduling, and canceling appointments effortlessly, integrating with external calendar services for maximum efficiency. Clients enjoy the flexibility of signing up via OAuth2 or secure traditional authentication, with comprehensive support for password management and secure recovery methodologies. TutorMate enforces GDPR-compliant data protection standards, ensuring user data is handled with the utmost care. Distinguishing between tutors and clients, it uses RBAC to tailor the app experience, granting appropriate access levels and functionalities. Financial management is robust, with features for invoice generation and tracking, payment processing, and detailed financial reporting. Real-time notifications keep all parties informed of significant events. Future-proofed for global use, its architecture is ready for multilingual support.\n\n### Features\n#### User Authentication\n##### Description\nSecure user sign-in and sign-up functionalities using OAuth2 and traditional methods, including encrypted password storage and GDPR-compliant data protection.\n##### Considerations\nChoosing secure, scalable authentication methods; ensuring user-friendly password reset and recovery options.\n##### Risks\nData breaches; non-compliance with GDPR.\n##### External Tools Required\nOAuth2 service providers; encryption libraries.\n##### Priority: CRITICAL\n#### Scheduling and Calendar Integration\n##### Description\nSupport for hourly slots, recurring appointments, and easy rescheduling or cancellation, synced with external calendar services.\n##### Considerations\nUser interface design for ease of use; integrating with popular calendar services.\n##### Risks\nSyncing issues with external services; user experience complexities.\n##### External Tools Required\nCalendar API integrations.\n##### Priority: HIGH\n#### Financial Management\n##### Description\nAutomated and customizable invoice generation and tracking, integrated with payment gateways for handling transactions.\n##### Considerations\nSelecting reliable payment gateways; designing flexible, user-friendly invoice management.\n##### Risks\nPayment processing errors; inaccurate financial tracking.\n##### External Tools Required\nPayment gateway APIs; invoice generation libraries.\n##### Priority: HIGH\n#### Role-Based Access Control (RBAC)\n##### Description\nImplementation of RBAC to ensure tutors and clients receive appropriate functionalities and views within the app.\n##### Considerations\nClearly defining roles and permissions; maintaining flexibility for future role additions.\n##### Risks\nInappropriate access levels; complexity in managing permissions.\n##### External Tools Required\nRBAC management libraries.\n##### Priority: CRITICAL\n#### Real-Time Notifications\n##### Description\nEfficient, scalable technology for sending real-time notifications about appointment updates, invoice statuses, and more.\n##### Considerations\nChoosing the right technology for scalability and efficiency; user settings for notification preferences.\n##### Risks\nNotification overload; technical challenges in real-time delivery.\n##### External Tools Required\nNotification services (e.g., push notifications, email, and SMS APIs).\n##### Priority: MEDIUM\n\n### Clarifiying Questions\n- "Do we need a front end for this: "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "yes" : Reasoning: "Considering the complexity and interactive nature of the described app functionality, including scheduling, authentication, invoice management, and report generation, a frontend is essential. It provides a user interface for both tutors and clients to interact with these features in an intuitive and efficient manner. The frontend would play a crucial role in facilitating the user experience, ensuring that the app is accessible, user-friendly, and secure, especially with the need for secure login processes and financial transactions."\n- "Who is the expected user of this: "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Tutors and their clients" : Reasoning: "For this application, the primary users are clearly defined as tutors and their clients. Tutors are the service providers looking for effective management of their schedules, clients, and financials. They require a platform that can handle appointment scheduling and rescheduling, invoice generation, and financial tracking in a consolidated manner. On the other hand, clients—who are receiving tutoring services—need a user-friendly interface to sign up, manage their appointments, and handle invoice payments. The mention of both OAuth2 and traditional sign-in methods caters to a wider preference in sign-in mechanisms, enhancing accessibility for all users. The application seeks to streamline the administrative aspect of tutoring services, offering distinct functionalities suited to the specific needs of tutors and clients, hence identifying them as the expected user personas."\n- "What is the skill level of the expected user of this: "The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices. It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed. Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities. There will need to be authorization for identifying clients vs the tutor. Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."": "Non-technical to moderately technical" : Reasoning: "Considering the description of The Tutor App, the expected skill level of its primary users—tutors and their clients—ranges from non-technical to moderately technical. The app appears to cater to individuals who are primarily focused on the tutoring aspect or seeking tutoring services, rather than on the technicalities of app usage. Features such as OAuth2 and traditional sign-in methods, along with password reset and login capabilities, are standard user interface components that most, if not all, app users should find intuitive to use. The mention of \'proper management of financials\' including invoicing and payment tracking suggests that users do not need specialized financial or technical expertise; instead, the app is expected to simplify these processes. Therefore, the design and functionality of the app must accommodate users who may not have a high level of technical skill but still require an efficient and straightforward method to manage scheduling, financials, and communication through the app."\n\n\n### Conclusive Q&A\n- "What level of granularity is required for the scheduling feature (e.g., time slots, recurring appointments)?": "Support for hourly slots, recurring appointments, and integration with external calendar services for availability checks." : Reasoning: "Scheduling is a core functionality. Understanding the required granularity helps in choosing the right technologies and designing an intuitive UI."\n- "Are there specific security requirements or standards for the traditional sign-in method?": "Implement best practices for web security, including encrypted password storage and secure recovery methods. Comply with GDPR for data protection." : Reasoning: "Security is paramount, especially for authentication. Clarifying this will guide the choice of technologies and implementation approach."\n- "How should the app differentiate between client and tutor roles, and are there differing levels of access or functionality?": "Use RBAC mechanisms to provide separate functionalities and views for tutors and clients, with tutors having more access and control." : Reasoning: "Role-based access control is essential for functionality and security. Understanding the differentiation helps in architecting the system properly."\n- "What specific functionalities are needed for invoice management and payment tracking?": "Automated invoice generation and tracking, with support for manual adjustments. Integrate with payment gateways for handling transactions." : Reasoning: "Invoice management and payment tracking can be complex, involving multiple external integration. Clarifying needed functionalities will ensure we meet user needs without overengineering."\n- "How detailed should the financial reports be (e.g., income breakdown by client, session type)?": "Flexible and customizable reporting features, including income breakdowns by various filters such as client and session type." : Reasoning: "Financial reporting needs can vary greatly. Understanding the level of detail and customization will impact database design and UI."\n- "Is there a requirement for real-time notifications for appointment changes and invoice statuses?": "Implement real-time notifications for key events such as appointment updates and invoice statuses using efficient, scalable technology." : Reasoning: "Real-time notifications can significantly enhance user experience but require careful architectural considerations."\n- "What mechanisms are to be included for unpaid invoice follow-up?": "Implement both automated and manual follow-up processes for unpaid invoices, using email and possibly SMS notifications." : Reasoning: "Manual versus automated follow-up can significantly differ in implementation complexity. Need to understand expectations."\n- "Will the app require multilingual support?": "Plan for English with a scalable architecture that supports adding more languages in the future." : Reasoning: "Considering the potential global user base, understanding multilingual needs is crucial for UI/UX design."\n- "Do tutors have the ability to set custom rates for different types of tutoring sessions?": "Include functionality for tutors to set custom rates for various session types, including dynamic adjustments." : Reasoning: "Custom rate settings can influence database design and how fees are calculated and presented to clients."\n- "How will the app handle cancellations and rescheduling to ensure fairness for both tutors and clients?": "Flexible yet defined cancellation and rescheduling policies supported by backend logic to enforce fairness and clarity." : Reasoning: "Cancellation and rescheduling policies can impact user satisfaction and operational complexity."\n\n\n### Requirement Q&A\n- "do we need db?": "Yes" : Reasoning: "We need a database to store user data, scheduling, and financial information. We also need to store communication data. We need a database."\n- "do we need an api for talking to a front end?": "Yes" : Reasoning: "Considering the requirement for a frontend, an API is essential for the frontend to communicate with the backend services securely and efficiently."\n- "do we need an api for talking to other services?": "Yes" : Reasoning: "Given the need for functionalities like payment gateway integration and possibly external calendar services, an API for talking to other services is required."\n- "do we need an api for other services talking to us?": "Yes" : Reasoning: "For functionalities like real-time notifications and possibly other integrations that may require external services to initiate communication, an API to allow this is necessary."\n- "do we need to issue api keys for other services to talk to us?": "Yes" : Reasoning: "To ensure secure communication and control access, issuing API keys to other services is necessary."\n- "do we need monitoring?": "Yes" : Reasoning: "Monitoring is essential to maintain the health of the application, monitor its performance, and quickly address any issues that arise."\n- "do we need internationalization?": "Yes" : Reasoning: "While initially planning for English, the architecture should be scalable to add more languages in the future, indicating the need for internationalization preparation."\n- "do we need analytics?": "Yes" : Reasoning: "Analytics are crucial for understanding user behavior, app performance, and guiding future developments based on data-driven insights."\n- "is there monetization?": "Yes" : Reasoning: "Considering the requirement for managing financials and possibly monetizing through premium features, there is an indication of monetization."\n- "is the monetization via a paywall or ads?": "Paywall" : Reasoning: "Given the context and requirement for a professional angle focusing on the service provided rather than interrupting user experience, a paywall for premium features or services is more suitable than ads."\n- "does this require a subscription or a one-time purchase?": "Subscription" : Reasoning: "To maintain a steady income and provide ongoing services and updates, a subscription model fits better than a one-time purchase."\n- "is the whole service monetized or only part?": "Part" : Reasoning: "To ensure broad accessibility while also enabling a revenue stream, only part of the service should be monetized, offering both free and premium features."\n- "is monetization implemented through authorization?": "Yes" : Reasoning: "Differentiating between free and premium users to control access to certain features requires monetization to be tied into the authorization system."\n- "do we need authentication?": "Yes" : Reasoning: "Given the need for secure user profiles, along with differentiating between tutors and clients, authentication is necessary."\n- "do we need authorization?": "Yes" : Reasoning: "To differentiate between the functionalities available to different user roles like tutors and clients, authorization is crucial."\n- "what authorization roles do we need?": "["Tutor", "Client"]" : Reasoning: "Considering the functionalities specified and the need to differentiate user experiences and access rights, we need separate roles for tutors and clients."\n\n\n### Requirements\n### Functional Requirements\n#### User Authentication\n##### Thoughts\nThe cornerstone for securing user data and offering a seamless yet secure access to the platform.\n##### Description\nSecure user sign-in and sign-up functionalities using OAuth2 and traditional methods, including encrypted password storage and GDPR-compliant data protection.\n#### Scheduling and Calendar Integration\n##### Thoughts\nVital for the core functionality of managing tutoring sessions efficiently.\n##### Description\nSupport for hourly slots, recurring appointments, and easy rescheduling or cancellation, synced with external calendar services.\n#### Financial Management\n##### Thoughts\nEnsures tutors are compensated timely and properly without manual errors.\n##### Description\nAutomated and customizable invoice generation and tracking, integrated with payment gateways for handling transactions.\n#### Role-Based Access Control (RBAC)\n##### Thoughts\nCrucial for user experience customization based on the role of the user, enhancing security and functionality.\n##### Description\nImplementation of RBAC to ensure tutors and clients receive appropriate functionalities and views within the app.\n#### Real-Time Notifications\n##### Thoughts\nImproves user engagement and keeps all parties promptly informed of critical updates.\n##### Description\nEfficient, scalable technology for sending real-time notifications about appointment updates, invoice statuses, and more.\n#### Flexible Financial Reporting\n##### Thoughts\nSupports better financial planning and review for tutors.\n##### Description\nCustomizable financial reporting features for tracking and analyzing income, with various filters like client and session type.\n#### Multi-Language Support\n##### Thoughts\nEssential for scaling the app in different regions and improving accessibility.\n##### Description\nAn architecture that accommodates multiple languages, starting with English, to cater to a global user base.\n\n### Nonfunctional Requirements\n#### Scalability\n##### Thoughts\nA crucial quality for handling peak loads smoothly and sustaining growth.\n##### Description\nThe system must be able to scale horizontally to accommodate an increasing number of users and appointments.\n#### Security\n##### Thoughts\nNon-negotiable to protect user privacy and build trust.\n##### Description\nAdhere to stringent security protocols for user data protection, including GDPR compliance and encrypted data transmissions.\n#### Usability\n##### Thoughts\nDirectly impacts user adoption and satisfaction.\n##### Description\nThe app interface should be intuitive and accessible for users of varying technical abilities, requiring minimal training to use effectively.\n#### Performance\n##### Thoughts\nEssential for a seamless user experience, especially for time-critical features.\n##### Description\nEnsure low latency and high responsiveness of the app, particularly for scheduling functionalities and real-time notifications.\n#### Maintainability\n##### Thoughts\nFacilitates easier maintenance and upgrades, reducing long-term costs.\n##### Description\nCodebase and architecture should be designed for easy updates, scalability, and bug fixes, adhering to best coding practices.\n#### Integration Capability\n##### Thoughts\nEssential for extending functionality without reinventing the wheel.\n##### Description\nThe app must be capable of integrating seamlessly with external APIs and services, such as calendar and payment gateways.\n#### Data Integrity\n##### Thoughts\nCrucial for reliability and minimizing disputes or confusion.\n##### Description\nThe system must ensure data accuracy, especially in financial transactions and scheduling information.\n\n\n### Modules\n### Module: AuthModule\n#### Description\nThe AuthModule handles all aspects of authentication, supporting both OAuth2 and traditional sign-up/sign-in mechanisms. It ensures the security of user credentials, supports password recovery, and complies with GDPR for user data protection.\n#### Requirements\n#### Requirement: OAuth2 Integration\nImplement OAuth2 integration for enabling users to sign up and log in using their social accounts.\n\n#### Requirement: Traditional Authentication\nSupport traditional sign-up/sign-in mechanisms with encrypted password storage and secure recovery processes.\n\n#### Requirement: GDPR Compliance\nEnsure all authentication processes comply with GDPR, emphasizing user data protection and privacy.\n\n#### Requirement: User Session Management\nManage user sessions to keep users logged in securely, with options for logout and session timeouts.\n\n#### Endpoints\n##### sign_up_with_oauth2: `POST /auth/signup/oauth2`\n\nRegisters a new user using OAuth2 authentication.\n\n\n\n\n\n\n##### sign_up_with_email: `POST /auth/signup/email`\n\nRegisters a new user with traditional email and password method.\n\n\n\n\n\n\n##### sign_in: `POST /auth/signin`\n\nAuthenticates a user, returning a secure token.\n\n\n\n\n\n\n##### password_reset: `POST /auth/reset`\n\nInitiates a password reset process for users with traditional authentication.\n\n\n\n\n\n\n\n### Module: UserModule\n#### Description\nThe UserModule is responsible for managing user profiles, including the storage, retrieval, and update of user data. It handles role assignment and enforces appropriate access levels for different user types within the platform.\n#### Requirements\n#### Requirement: User Profile Management\nEnables creation, updating, and retrieval of user profiles.\n\n#### Requirement: Role Assignment\nAssigns roles to users (Tutor or Client) to determine the access level and functionalities available to them.\n\n#### Requirement: User Data Integrity\nEnsures the integrity and security of user data, adhering to privacy standards.\n\n#### Endpoints\n##### create_user_profile: `POST /user/profile`\n\nCreates a new user profile.\n\n\n\n\n\n\n##### update_user_profile: `PUT /user/profile/{id}`\n\nUpdates an existing user profile.\n\n\n\n\n\n\n##### get_user_profile: `GET /user/profile/{id}`\n\nRetrieves a user\'s profile data.\n\n\n\n\n\n\n##### update_user_settings: `PUT /user/settings/{id}`\n\nUpdates user-specific settings, such as language preference.\n\n\n\n\n\n\n\n### Module: AppointmentModule\n#### Description\nCore to the scheduling functionality, this module handles creating, updating, cancelling, and viewing appointments. It integrates with external calendar services to reflect real-time availability and manages the logistics of appointment timings, rescheduling, and recurring appointments.\n\n### Module: InvoiceModule\n#### Description\nFacilitates creation and management of invoices. This includes tracking of paid and unpaid statuses, integrating with payment gateways for transactions, and providing tutors with the ability to generate financial reports. It emphasizes automated invoice processing with support for manual adjustments.\n\n### Module: NotificationModule\n#### Description\nSends real-time notifications to tutors and clients regarding key events such as appointment changes, invoice statuses, and payment reminders. This module is essential for keeping all parties informed and engaged, using efficient, scalable technology for notification delivery.\n\n### Module: FinancialReportModule\n#### Description\nSupplies tutors with the ability to generate customizable financial reports based on various filters, such as income by client or session type. This module supports better financial planning and review, enhancing the tutors\' ability to manage their incomes.\n\n### Module: IntegrationModule\n#### Description\nServes as the integration point with external APIs and services, such as calendar services and payment gateways. This module plays a crucial role in ensuring smooth interoperability with third-party services, centralizing integration logic.\n\n### Module: LanguageSupportModule\n#### Description\nManages the multi-language support for the application, enabling dynamic language selection and storing interface translations. This module will allow TutorMate to cater to a global user base by providing localized experiences.\n\n### Database Design\n## TutorAppSchema\n**Description**: This Schema is designed to manage users, appointments, invoices, and payments for a Tutor App. It includes role-based access and supports OAuth2 authentication. Additionally, it handles financial tracking and real-time notifications.\n**Tables**:\n**User**\n\n**Description**: Stores user details including authentication information and preferences.\n\n**Definition**:\n```\nmodel User {\n  id                String              @id @default(uuid())\n  email             String              @unique\n  password          String?\n  role              UserRole\n  languagePreference String? @default("en")\n  OAuthId           String?\n  appointments      Appointment[]\n  invoices          Invoice[]\n  notifications     Notification[]\n}\n```\n\n**Appointment**\n\n**Description**: Manages appointment details including scheduling, status, and related users.\n\n**Definition**:\n```\nmodel Appointment {\n  id          String           @id @default(uuid())\n  tutorId     String\n  clientId    String\n  status      AppointmentStatus\n  startTime   DateTime\n  endTime     DateTime\n  invoice     Invoice?\n}\n```\n\n**Invoice**\n\n**Description**: Handles invoice creation, status, and tracks associated payments.\n\n**Definition**:\n```\nmodel Invoice {\n  id           String     @id @default(uuid())\n  appointmentId String\n  amount       Float\n  status       InvoiceStatus\n  createdAt    DateTime  @default(now())\n  updatedAt    DateTime  @updatedAt\n  payments     Payment[]\n}\n```\n\n**Payment**\n\n**Description**: Records payment transactions against invoices.\n\n**Definition**:\n```\nmodel Payment {\n  id          String      @id @default(uuid())\n  invoiceId   String\n  status      PaymentStatus\n  amount      Float\n  paymentDate DateTime\n}\n```\n\n**Notification**\n\n**Description**: Stores notifications to be sent to users for updates or reminders.\n\n**Definition**:\n```\nmodel Notification {\n  id      String   @id @default(uuid())\n  userId  String\n  content String\n  sentAt  DateTime\n}\n```\n\n**UserRole**\n\n**Description**: Defines the roles a user can have in the app, distinguishing between tutors and clients.\n\n**Definition**:\n```\nenum UserRole {\n  Tutor\n  Client\n}\n```\n\n**AppointmentStatus**\n\n**Description**: Tracks the status of appointments.\n\n**Definition**:\n```\nenum AppointmentStatus {\n  Scheduled\n  Completed\n  Cancelled\n}\n```\n\n**InvoiceStatus**\n\n**Description**: Indicates the payment status of invoices.\n\n**Definition**:\n```\nenum InvoiceStatus {\n  Pending\n  Paid\n  Failed\n}\n```\n\n**PaymentStatus**\n\n**Description**: Captures the result of a payment transaction.\n\n**Definition**:\n```\nenum PaymentStatus {\n  Successful\n  Failed\n}\n```\n\n',
        "db_models": "[User,Appointment,Invoice,Payment,Notification,UserRole,AppointmentStatus,InvoiceStatus,PaymentStatus]",
        "db_enums": "[UserRole,AppointmentStatus,InvoiceStatus,PaymentStatus]",
        "module_repr": "Module(name='AuthModule', description='The AuthModule handles all aspects of authentication, supporting both OAuth2 and traditional sign-up/sign-in mechanisms. It ensures the security of user credentials, supports password recovery, and complies with GDPR for user data protection.', requirements=[ModuleRefinementRequirement(name='OAuth2 Integration', description='Implement OAuth2 integration for enabling users to sign up and log in using their social accounts.'), ModuleRefinementRequirement(name='Traditional Authentication', description='Support traditional sign-up/sign-in mechanisms with encrypted password storage and secure recovery processes.'), ModuleRefinementRequirement(name='GDPR Compliance', description='Ensure all authentication processes comply with GDPR, emphasizing user data protection and privacy.'), ModuleRefinementRequirement(name='User Session Management', description='Manage user sessions to keep users logged in securely, with options for logout and session timeouts.')], endpoints=[Endpoint(name='sign_up_with_oauth2', type='POST', description='Registers a new user using OAuth2 authentication.', path='/auth/signup/oauth2', request_model=None, response_model=None, database_schema=None), Endpoint(name='sign_up_with_email', type='POST', description='Registers a new user with traditional email and password method.', path='/auth/signup/email', request_model=None, response_model=None, database_schema=None), Endpoint(name='sign_in', type='POST', description='Authenticates a user, returning a secure token.', path='/auth/signin', request_model=None, response_model=None, database_schema=None), Endpoint(name='password_reset', type='POST', description='Initiates a password reset process for users with traditional authentication.', path='/auth/reset', request_model=None, response_model=None, database_schema=None)], related_modules=[])",
        "endpoint_repr": "Endpoint(name='sign_up_with_oauth2', type='POST', description='Registers a new user using OAuth2 authentication.', path='/auth/signup/oauth2', request_model=None, response_model=None, database_schema=None)",
    }
    endpoint_block = EndpointSchemaRefinementBlock()

    async def run_ai() -> dict[str, EndpointSchemaRefinementResponse]:
        if not db_client.is_connected():
            await db_client.connect()
        endpoint1_ref: EndpointSchemaRefinementResponse = await endpoint_block.invoke(
            ids=ids,
            invoke_params=invoke_params,
        )

        await db_client.disconnect()
        return {"endpoint1": endpoint1_ref}

    endpoints = run(run_ai())

    for key, item in endpoints.items():
        if isinstance(item, EndpointSchemaRefinementResponse):
            logger.info("Endpoint:")
            logger.info(f"\tThink: {item.think}")
            logger.info(f"\tDB Models Needed: {item.db_models_needed}")
            logger.info(f"\tEnd Thoughts: {item.end_thoughts}")
            logger.info("\tAPI Endpoint Request: ")
            # Request Model
            logger.info(f"\t\t{item.api_endpoint.request_model}")
            logger.info(
                f"\t\tRequest Model Name: {item.api_endpoint.request_model.name}"
            )
            logger.info(
                f"\t\tRequest Model Description: {item.api_endpoint.request_model.description}"
            )
            logger.info(
                f"\t\tRequest Model Fields: {item.api_endpoint.request_model.Fields}"
            )
            # This shouldn't be longer than this Surely
            for i in item.api_endpoint.request_model.Fields or []:
                logger.info(f"\t\t\t{i}")
                logger.info(f"\t\t\tField Name: {i.name}")
                logger.info(f"\t\t\tField Description: {i.description}")
                logger.info(f"\t\t\tField Type: {i.type}")
                logger.info(f"\t\t\tField Related Types: {i.related_types!r}")
                for j in i.related_types or []:
                    logger.info(f"\t\t\t\t{j}")
                    logger.info(f"\t\t\t\tRelated Type Name: {j.name}")
                    logger.info(f"\t\t\t\tRelated Type Description: {j.description}")
                    logger.info(f"\t\t\t\tRelated Type Fields: {j.Fields}")
                    for k in j.Fields or []:
                        logger.info(f"\t\t\t\t\t{k}")
                        logger.info(f"\t\t\t\t\tField Name: {k.name}")
                        logger.info(f"\t\t\t\t\tField Description: {k.description}")
                        logger.info(f"\t\t\t\t\tField Type: {k.type}")
                        logger.info(
                            f"\t\t\t\t\tField Related Types: {k.related_types!r}"
                        )
                        for z in k.related_types or []:
                            logger.info(f"\t\t\t\t\t\t{z}")
                            logger.info(f"\t\t\t\t\t\tRelated Type Name: {z.name}")
                            logger.info(
                                f"\t\t\t\t\t\tRelated Type Description: {z.description}"
                            )
                            logger.info(f"\t\t\t\t\t\tRelated Type Fields: {z.Fields}")
                            for m in z.Fields or []:
                                logger.info(f"\t\t\t\t\t\t\t{m}")
                                logger.info(f"\t\t\t\t\t\t\tField Name: {m.name}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Description: {m.description}"
                                )
                                logger.info(f"\t\t\t\t\t\t\tField Type: {m.type}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Related Types: {m.related_types!r}"
                                )
                                if len(m.related_types or []) > 0:
                                    logger.info("This is insanely recursive")
                                    breakpoint()
            logger.info("\tAPI Endpoint Response:")
            # Response Model
            logger.info(f"\t\t{item.api_endpoint.response_model}")
            logger.info(
                f"\t\tResponse Model Name: {item.api_endpoint.response_model.name}"
            )
            logger.info(
                f"\t\tResponse Model Description: {item.api_endpoint.response_model.description}"
            )
            logger.info(
                f"\t\tResponse Model Fields: {item.api_endpoint.response_model.Fields}"
            )
            # This shouldn't be longer than this Surely
            for i in item.api_endpoint.response_model.Fields or []:
                logger.info(f"\t\t\t{i}")
                logger.info(f"\t\t\tField Name: {i.name}")
                logger.info(f"\t\t\tField Description: {i.description}")
                logger.info(f"\t\t\tField Type: {i.type}")
                logger.info(f"\t\t\tField Related Types: {i.related_types!r}")
                for j in i.related_types or []:
                    logger.info(f"\t\t\t\t{j}")
                    logger.info(f"\t\t\t\tRelated Type Name: {j.name}")
                    logger.info(f"\t\t\t\tRelated Type Description: {j.description}")
                    logger.info(f"\t\t\t\tRelated Type Fields: {j.Fields}")
                    for k in j.Fields or []:
                        logger.info(f"\t\t\t\t\t{k}")
                        logger.info(f"\t\t\t\t\tField Name: {k.name}")
                        logger.info(f"\t\t\t\t\tField Description: {k.description}")
                        logger.info(f"\t\t\t\t\tField Type: {k.type}")
                        logger.info(
                            f"\t\t\t\t\tField Related Types: {k.related_types!r}"
                        )
                        for z in k.related_types or []:
                            logger.info(f"\t\t\t\t\t\t{z}")
                            logger.info(f"\t\t\t\t\t\tRelated Type Name: {z.name}")
                            logger.info(
                                f"\t\t\t\t\t\tRelated Type Description: {z.description}"
                            )
                            logger.info(f"\t\t\t\t\t\tRelated Type Fields: {z.Fields}")
                            for m in z.Fields or []:
                                logger.info(f"\t\t\t\t\t\t\t{m}")
                                logger.info(f"\t\t\t\t\t\t\tField Name: {m.name}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Description: {m.description}"
                                )
                                logger.info(f"\t\t\t\t\t\t\tField Type: {m.type}")
                                logger.info(
                                    f"\t\t\t\t\t\t\tField Related Types: {m.related_types!r}"
                                )
                                if len(m.related_types or []) > 0:
                                    logger.info("????")
                                    breakpoint()
            logger.info("\n\n\n")
        else:
            logger.info("????")
            breakpoint()

    # # If you want to test the block in an interactive environment
    # import IPython

    # IPython.embed()
    breakpoint()
