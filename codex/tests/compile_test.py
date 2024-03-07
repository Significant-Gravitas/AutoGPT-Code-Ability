from datetime import datetime

import pytest
from prisma.models import ObjectField, ObjectType

from codex.develop.function import generate_object_template
from codex.develop.compile import extract_path_params, get_object_type_deps


async def process_object_type(obj: ObjectType) -> str:
    objects = await get_object_type_deps(obj, set()) + [obj]
    return "\n\n".join([generate_object_template(v) for v in objects])


@pytest.mark.asyncio
async def test_process_object_type():
    obj = ObjectType(
        id="a",
        createdAt=datetime.now(),
        name="Person",
        description="Represents a person",
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

    pydantic_output = await process_object_type(obj)
    expected_output = """class Person(BaseModel):
    \"\"\"
    Represents a person
    \"\"\"
    name: str  # The name of the person
    age: int  # The age of the person"""
    assert (
        pydantic_output == expected_output
    ), f"Expected {pydantic_output} to be {expected_output}"


def test_extract_path_parameters():
    url = "/api/va/user/{user_id}/app/{app_id}/build"
    params = extract_path_params(url)

    assert len(params) == 2, f"Expected {len(params)} to be 2"
    assert params == [
        "user_id",
        "app_id",
    ], f"Expected {params} to be ['user_id', 'app_id']"
