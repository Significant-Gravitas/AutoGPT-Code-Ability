from datetime import datetime

from prisma.models import ObjectField, ObjectType

from codex.develop.compile import (
    add_full_import_parth_to_custom_types,
    extract_path_params,
)
from codex.develop.function import generate_object_template


def test_process_object_type():
    obj = ObjectType(
        id="a",
        createdAt=datetime.now(),
        name="Person",
        description="Represents a person",
        isPydantic=True,
        isEnum=False,
        Fields=[
            ObjectField(
                name="name",
                typeName="str",
                description="The name of the person",
                id="a",
                createdAt=datetime.now(),
                referredObjectTypeId="a",
            ),
            ObjectField(
                name="age",
                typeName="int",
                description="The age of the person",
                id="a",
                createdAt=datetime.now(),
                referredObjectTypeId="a",
            ),
        ],
        importStatements=[],
    )

    pydantic_output = generate_object_template(obj)
    expected_output = """class Person(BaseModel):
    \"\"\"
    Represents a person
    \"\"\"
    name: str  # The name of the person
    age: int  # The age of the person"""
    assert (
        pydantic_output == expected_output
    ), f"Expected {pydantic_output} to be {expected_output}"


def test_process_enum_type():
    obj = ObjectType(
        id="a",
        createdAt=datetime.now(),
        name="Role",
        description="Represents a role",
        isEnum=True,
        isPydantic=False,
        Fields=[
            ObjectField(
                name="ADMIN",
                typeName="str",
                description="The admin role",
                id="a",
                createdAt=datetime.now(),
                referredObjectTypeId="a",
            ),
            ObjectField(
                name="USER",
                typeName="str",
                description="The user role",
                id="a",
                createdAt=datetime.now(),
                referredObjectTypeId="a",
            ),
        ],
        importStatements=[],
    )

    output = generate_object_template(obj)
    expected_output = """class Role(Enum):
    \"\"\"
    Represents a role
    \"\"\"
    ADMIN: str  # The admin role
    USER: str  # The user role"""
    assert output == expected_output, f"Expected {output} to be {expected_output}"


def test_extract_path_parameters():
    url = "/api/va/user/{user_id}/app/{app_id}/build"
    params = extract_path_params(url)

    assert len(params) == 2, f"Expected {len(params)} to be 2"
    assert params == [
        "user_id",
        "app_id",
    ], f"Expected {params} to be ['user_id', 'app_id']"


def test_return_type_no_related_types():
    # Arrange
    module_name = "project"
    arg = ObjectField(
        name="arg1", typeName="int", RelatedTypes=None, id="1", createdAt=datetime.now()
    )

    # Act
    result = add_full_import_parth_to_custom_types(module_name, arg)

    # Assert
    assert result == "int"


def test_arg_type_with_related_type_fixed():
    # Arrange
    module_name = "project"
    t = ObjectType(
        id="asd",
        createdAt=datetime.now(),
        isPydantic=True,
        isEnum=False,
        name="RelatedType",
        importStatements=[],
    )
    arg = ObjectField(
        id="asd",
        createdAt=datetime.now(),
        name="arg1",
        typeName="RelatedType",
        RelatedTypes=[t],
    )

    # Act
    result = add_full_import_parth_to_custom_types(module_name, arg)

    # Assert
    assert result == "project.RelatedType"


def test_multiple_related_types():
    # Arrange
    module_name = "project"
    t1 = ObjectType(
        id="asd",
        createdAt=datetime.now(),
        isPydantic=True,
        isEnum=False,
        name="RelatedType1",
        importStatements=[],
    )
    t2 = ObjectType(
        id="asd",
        createdAt=datetime.now(),
        isPydantic=True,
        isEnum=False,
        name="RelatedType2",
        importStatements=[],
    )
    arg = ObjectField(
        id="asd",
        createdAt=datetime.now(),
        name="arg1",
        typeName="Tuple[RelatedType1, RelatedType2]",
        RelatedTypes=[t1, t2],
    )

    # Act
    result = add_full_import_parth_to_custom_types(module_name, arg)

    # Assert
    assert result == "Tuple[project.RelatedType1, project.RelatedType2]"


def test_multiple_related_types_with_similiar_name():
    # Arrange
    module_name = "project"
    t1 = ObjectType(
        id="asd",
        createdAt=datetime.now(),
        isPydantic=True,
        isEnum=False,
        name="User",
        importStatements=[],
    )
    t2 = ObjectType(
        id="asd",
        createdAt=datetime.now(),
        isPydantic=True,
        isEnum=False,
        name="UserProfile",
        importStatements=[],
    )
    arg = ObjectField(
        id="asd",
        createdAt=datetime.now(),
        name="arg1",
        typeName="Tuple[User, UserProfile]",
        RelatedTypes=[t1, t2],
    )

    # Act
    result = add_full_import_parth_to_custom_types(module_name, arg)

    # Assert
    assert result == "Tuple[project.User, project.UserProfile]"
