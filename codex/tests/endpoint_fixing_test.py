import codex.requirements.blocks.ai_endpoint
from codex.api_model import ObjectFieldModel, ObjectTypeModel
from codex.requirements.blocks.ai_endpoint import parse_object_model


def test_simple_fix_any_Any():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="Dict[str, any]",
                related_types=[],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

    (
        request_types,
        response_types,
        request_object_types,
        response_object_types,
        new_request_model,
        new_response_model,
        invalid_request_types,
        invalid_response_types,
    ) = parse_object_model(request_model, response_model, allowed_types)

    assert len(request_types) == 4
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 1
    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "Dict[str, Any]"
    assert new_request_model.Fields[0].related_types == []

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_using_model_not_in_db():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="FakeTableModel",
                related_types=[],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

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
        request_model=request_model,
        response_model=response_model,
        allowed_types=allowed_types,
    )

    assert len(request_types) == 2
    assert len(response_types) == 2
    assert invalid_request_types == ["FakeTableModel"]
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 1
    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "FakeTableModel"
    assert new_request_model.Fields[0].related_types == []

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_filling_out_same_model_dict():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="Dict[str, House]",
                related_types=[],
            ),
            ObjectFieldModel(
                name="test",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[
                    ObjectTypeModel(
                        name="House",
                        description="A house model for testing.",
                        Fields=[
                            ObjectFieldModel(
                                name="type",
                                description="The type of the access token provided. Typically 'Bearer'.",
                                type="str",
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

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
        request_model=request_model,
        response_model=response_model,
        allowed_types=allowed_types,
    )

    assert len(request_types) == 4
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 2

    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "Dict[str, House]"
    assert new_request_model.Fields[0].related_types
    assert len(new_request_model.Fields[0].related_types) == 1
    assert new_request_model.Fields[0].related_types[0].name == "House"
    assert new_request_model.Fields[0].related_types[0].Fields
    assert len(new_request_model.Fields[0].related_types[0].Fields) == 1
    assert new_request_model.Fields[0].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[0].related_types[0].Fields[0].type == "str"

    assert new_request_model.Fields[1].name == "test"
    assert new_request_model.Fields[1].type == "House"
    assert new_request_model.Fields[1].related_types
    assert len(new_request_model.Fields[1].related_types) == 1
    assert new_request_model.Fields[1].related_types[0].name == "House"
    assert new_request_model.Fields[1].related_types[0].Fields
    assert len(new_request_model.Fields[1].related_types[0].Fields) == 1
    assert new_request_model.Fields[1].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[1].related_types[0].Fields[0].type == "str"

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_filling_out_same_model_simple_model_first():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[
                    ObjectTypeModel(
                        name="House",
                        description="A house model for testing.",
                        Fields=[
                            ObjectFieldModel(
                                name="type",
                                description="The type of the access token provided. Typically 'Bearer'.",
                                type="str",
                            )
                        ],
                    )
                ],
            ),
            ObjectFieldModel(
                name="test",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

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
        request_model=request_model,
        response_model=response_model,
        allowed_types=allowed_types,
    )

    assert len(request_types) == 3
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 2

    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "House"
    assert new_request_model.Fields[0].related_types
    assert len(new_request_model.Fields[0].related_types) == 1
    assert new_request_model.Fields[0].related_types[0].name == "House"
    assert new_request_model.Fields[0].related_types[0].Fields
    assert len(new_request_model.Fields[0].related_types[0].Fields) == 1
    assert new_request_model.Fields[0].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[0].related_types[0].Fields[0].type == "str"

    assert new_request_model.Fields[1].name == "test"
    assert new_request_model.Fields[1].type == "House"
    assert new_request_model.Fields[1].related_types
    assert len(new_request_model.Fields[1].related_types) == 1
    assert new_request_model.Fields[1].related_types[0].name == "House"
    assert new_request_model.Fields[1].related_types[0].Fields
    assert len(new_request_model.Fields[1].related_types[0].Fields) == 1
    assert new_request_model.Fields[1].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[1].related_types[0].Fields[0].type == "str"

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_filling_out_same_model_simple_model_last():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[],
            ),
            ObjectFieldModel(
                name="test",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[
                    ObjectTypeModel(
                        name="House",
                        description="A house model for testing.",
                        Fields=[
                            ObjectFieldModel(
                                name="type",
                                description="The type of the access token provided. Typically 'Bearer'.",
                                type="str",
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

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
        request_model=request_model,
        response_model=response_model,
        allowed_types=allowed_types,
    )

    assert len(request_types) == 3
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 2

    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "House"
    assert new_request_model.Fields[0].related_types
    assert len(new_request_model.Fields[0].related_types) == 1
    assert new_request_model.Fields[0].related_types[0].name == "House"
    assert new_request_model.Fields[0].related_types[0].Fields
    assert len(new_request_model.Fields[0].related_types[0].Fields) == 1
    assert new_request_model.Fields[0].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[0].related_types[0].Fields[0].type == "str"

    assert new_request_model.Fields[1].name == "test"
    assert new_request_model.Fields[1].type == "House"
    assert new_request_model.Fields[1].related_types
    assert len(new_request_model.Fields[1].related_types) == 1
    assert new_request_model.Fields[1].related_types[0].name == "House"
    assert new_request_model.Fields[1].related_types[0].Fields
    assert len(new_request_model.Fields[1].related_types[0].Fields) == 1
    assert new_request_model.Fields[1].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[1].related_types[0].Fields[0].type == "str"

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_cross_model():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="House",
                related_types=[
                    ObjectTypeModel(
                        name="House",
                        description="A house model for testing.",
                        Fields=[
                            ObjectFieldModel(
                                name="type",
                                description="The type of the access token provided. Typically 'Bearer'.",
                                type="str",
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="House",
                related_types=[],
            ),
        ],
    )

    (
        request_types,
        response_types,
        request_object_types,
        response_object_types,
        new_request_model,
        new_response_model,
        invalid_request_types,
        invalid_response_types,
    ) = parse_object_model(request_model, response_model, allowed_types)

    assert len(request_types) == 3
    assert len(response_types) == 3
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 1
    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "House"
    assert new_request_model.Fields[0].related_types
    assert len(new_request_model.Fields[0].related_types) == 1
    assert new_request_model.Fields[0].related_types[0].name == "House"
    assert new_request_model.Fields[0].related_types[0].Fields
    assert len(new_request_model.Fields[0].related_types[0].Fields) == 1
    assert new_request_model.Fields[0].related_types[0].Fields[0].name == "type"
    assert new_request_model.Fields[0].related_types[0].Fields[0].type == "str"

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "House"
    assert new_response_model.Fields[0].related_types
    assert len(new_response_model.Fields[0].related_types) == 1
    assert new_response_model.Fields[0].related_types[0].name == "House"
    assert new_response_model.Fields[0].related_types[0].Fields
    assert len(new_response_model.Fields[0].related_types[0].Fields) == 1
    assert new_response_model.Fields[0].related_types[0].Fields[0].name == "type"
    assert new_response_model.Fields[0].related_types[0].Fields[0].type == "str"


def test_multilayer_type():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="Optional[Dict[str, bool]]",
                related_types=[],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

    (
        request_types,
        response_types,
        request_object_types,
        response_object_types,
        new_request_model,
        new_response_model,
        invalid_request_types,
        invalid_response_types,
    ) = parse_object_model(request_model, response_model, allowed_types)

    assert len(request_types) == 5
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 1
    assert new_request_model.Fields[0].name == "provider"
    assert new_request_model.Fields[0].type == "Optional[Dict[str, bool]]"
    assert new_request_model.Fields[0].related_types == []

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"


def test_multilayer_type_with_complexity():
    database_models = ["User", "Appointment", "Invoice", "Payment", "Notification"]
    database_enums = ["UserRole", "AppointmentStatus", "InvoiceStatus", "PaymentStatus"]
    allowed_types = (
        database_enums
        + database_models
        + codex.requirements.blocks.ai_endpoint.ALLOWED_TYPES
    )

    request_model = ObjectTypeModel(
        name="SignupWithOAuth2Request",
        description="This request model captures the necessary information for registering a new user through OAuth2 authentication. It includes the OAuth2 provider name and the token received from the provider.",
        Fields=[
            ObjectFieldModel(
                name="provider",
                description="The name of the OAuth2 provider (e.g., 'google', 'facebook').",
                type="Optional[Dict[Union[str, UserRole], Union[str, bool]]]",
                related_types=[],
            ),
        ],
    )
    response_model = ObjectTypeModel(
        name="SignupWithOAuth2Response",
        description="The response returned after a successful registration through OAuth2. It includes user details and an API token for subsequent requests.",
        Fields=[
            ObjectFieldModel(
                name="user_id",
                description="The unique identifier of the user in the system.",
                type="str",
                related_types=[],
            ),
        ],
    )

    (
        request_types,
        response_types,
        request_object_types,
        response_object_types,
        new_request_model,
        new_response_model,
        invalid_request_types,
        invalid_response_types,
    ) = parse_object_model(request_model, response_model, allowed_types)

    assert len(request_types) == 7
    assert len(response_types) == 2
    assert invalid_request_types == []
    assert invalid_response_types == []

    assert new_request_model.name == "SignupWithOAuth2Request"
    assert new_request_model.Fields
    assert len(new_request_model.Fields) == 1
    assert new_request_model.Fields[0].name == "provider"
    assert (
        new_request_model.Fields[0].type
        == "Optional[Dict[Union[str, UserRole], Union[str, bool]]]"
    )
    assert new_request_model.Fields[0].related_types == []

    assert new_response_model.name == "SignupWithOAuth2Response"
    assert new_response_model.Fields
    assert len(new_response_model.Fields) == 1
    assert new_response_model.Fields[0].name == "user_id"
    assert new_response_model.Fields[0].type == "str"
