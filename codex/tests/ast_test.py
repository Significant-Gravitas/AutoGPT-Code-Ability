import ast

from codex.develop.function_visitor import FunctionVisitor

SAMPLE_CODE = """
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class Location(BaseModel):
    name: str  # For named locations or coordinates as a string

class ProfessionalWorkingHours(BaseModel):
    professional_id: str
    start: datetime
    end: datetime

class Appointment(BaseModel):
    start_time: datetime
    end_time: datetime
    professional_id: str
    location: str

class TravelTime(BaseModel):
    start_location: str
    end_location: str
    time: timedelta

class SomeClass:
    start_location: str
    end_location: str
    time: timedelta


def calculate_travel_time(start_location: Location, end_location: Location) -> timedelta:
    \"\"\"
    Stub function to calculate the travel time between two locations.

    This function is intended to compute the estimated time it takes to travel from a start location to an end location.
    It can accept either named locations (e.g., "Office", "Home") or geographical coordinates in string format (e.g., "40.7128,-74.0060").
    The actual implementation of this function would involve complex logic possibly including API calls to mapping services,
    but in this stub, the specifics of how travel time is calculated are abstract.

    Args:
        start_location (str): The starting location's name or coordinates.
        end_location (str): The ending location's name or coordinates.

    Returns:
        timedelta: The estimated travel time between the two locations. For the purposes of this stub, a fixed
        travel time is returned to simulate functionality.

    Example:
        calculate_travel_time("Office", "Client Site")
        > timedelta(minutes=30)
    \"\"\"
    pass

def is_within_working_hours(
    professional_id: str,
    proposed_time: datetime,
    working_hours: Dict[str, ProfessionalWorkingHours]
) -> bool:
    \"\"\"
    Determination whether a proposed appointment time falls within a professional's predefined working hours.

    This function assesses the suitability of a proposed appointment time by comparing it with the professional's working
    hours. It is particularly useful in scheduling systems where appointments need to be set during specific hours.

    Args:
        professional_id (str): Unique identifier of the professional.
        proposed_time (datetime): The datetime object representing the proposed appointment time.
        working_hours (Dict[str, Tuple[datetime, datetime]]): A dictionary with professional_id as keys and tuples
        representing the start and end of working hours as values.

    Returns:
        bool: A boolean value indicating if the proposed_time falls within the working hours of the specified professional.

    Example:
        is_within_working_hours(
            "prof123",
            datetime(2023, 4, 15, 10, 0),
            {"prof123": (datetime(2023, 4, 15, 9, 0), datetime(2023, 4, 15, 17, 0))}
        )
        > True
    \"\"\"
    pass

def create_schedule(
    appointments: List[Appointment],
    working_hours: Dict[str, ProfessionalWorkingHours],
    travel_times: Dict[Tuple[str, str], TravelTime]
) -> List[Appointment]:
    \"\"\"
    pass
    \"\"\"
    suggested_appointments = []

    for prof_id, working_hour in working_hours.items():
        available_start = working_hour.start
        while available_start < working_hour.end:
            # Find end time by adding minimum appointment duration to start
            available_end = available_start + timedelta(hours=1)  # Assuming 1-hour appointments

            # Check if this slot is within working hours and not overlapping with existing appointments
            if is_within_working_hours(prof_id, available_start, working_hours) and all(
                not (appointment.start_time <= available_start < appointment.end_time or
                     appointment.start_time < available_end <= appointment.end_time)
                for appointment in appointments if appointment.professional_id == prof_id
            ):
                # Assuming all appointments are at the same location for simplification
                # In a real scenario, you would check travel times between locations here
                suggested_appointments.append(Appointment(
                    start_time=available_start,
                    end_time=available_end,
                    professional_id=prof_id,
                    location="Assumed Single Location"  # Placeholder
                ))
                # Adjust start time for next potential slot by considering travel time
                available_start = available_end + timedelta(minutes=30)  # Assuming fixed travel time for simplification
            else:
                # Move to the next slot if this one is not suitable
                available_start += timedelta(minutes=15)  # Check every 15 minutes for availability

    return suggested_appointments
"""


def test_function_visitor():
    tree = ast.parse(SAMPLE_CODE)

    visitor = FunctionVisitor()
    visitor.visit(tree)
    functions = {f.name: f for f in visitor.functions}

    # Check that all Pydantic classes are identified
    assert "SomeClass" not in get_pydantic_classes(visitor)
    assert "ProfessionalWorkingHours" in get_pydantic_classes(visitor)

    # Check that all functions are identified
    assert len(get_pydantic_classes(visitor)) == 4
    assert len(functions) == 3

    assert functions["create_schedule"].is_implemented
    assert not functions["is_within_working_hours"].is_implemented
    assert not functions["calculate_travel_time"].is_implemented

    # Assert detail for calculate_travel_time
    func = functions["calculate_travel_time"]
    assert func.name == "calculate_travel_time"
    assert func.arg_types == [
        ("start_location", "Location"),
        ("end_location", "Location"),
    ]
    assert func.arg_descs == {
        "start_location": "The starting location's name or coordinates.",
        "end_location": "The ending location's name or coordinates.",
    }
    assert func.return_type == "timedelta"
    assert func.return_desc.startswith("The estimated travel time between")
    assert func.return_desc.endswith("time is returned to simulate functionality.")
    assert func.function_desc.startswith("Stub function to calculate the travel time")
    assert func.function_desc.endswith("how travel time is calculated are abstract.")


CLASS_AND_ENUM_SAMPLE_CODE = """
from pydantic import BaseModel
from enum import Enum

class Location(BaseModel):
    name: str  # For named locations or coordinates as a string
    latitude: float = 0.0
    longitude: float = 0.0
    
class Role(Enum):
    USER = 'USER'
    ADMIN = 'ADMIN'
"""


def test_function_visitor_with_enum():
    tree = ast.parse(CLASS_AND_ENUM_SAMPLE_CODE)

    visitor = FunctionVisitor()
    visitor.visit(tree)
    objects = {f.name: f for f in visitor.objects}

    # Check that all Pydantic classes are identified
    assert "Location" in objects
    assert "Role" in objects

    # Check that all objects are identified
    assert len(get_pydantic_classes(visitor)) == 1
    assert len(visitor.functions) == 0

    assert objects["Location"].is_pydantic
    assert objects["Role"].is_enum

    assert objects["Location"].Fields[0].name == "name"  # type: ignore
    assert objects["Location"].Fields[0].type == "str"  # type: ignore
    assert objects["Location"].Fields[0].value is None  # type: ignore
    assert objects["Location"].Fields[1].name == "latitude"  # type: ignore
    assert objects["Location"].Fields[1].type == "float"  # type: ignore
    assert objects["Location"].Fields[1].value == "0.0"  # type: ignore
    assert objects["Location"].Fields[2].name == "longitude"  # type: ignore
    assert objects["Location"].Fields[2].type == "float"  # type: ignore
    assert objects["Location"].Fields[2].value == "0.0"  # type: ignore
    assert objects["Role"].Fields[0].name == "USER"  # type: ignore
    assert objects["Role"].Fields[0].type == "str"  # type: ignore
    assert objects["Role"].Fields[0].value == "'USER'"  # type: ignore
    assert objects["Role"].Fields[1].name == "ADMIN"  # type: ignore
    assert objects["Role"].Fields[1].type == "str"  # type: ignore
    assert objects["Role"].Fields[1].value == "'ADMIN'"  # type: ignore


# Visiting a simple function definition with no arguments or return type
def test_simple_function_definition():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a simple function definition
    code = ast.parse("def my_function():\n    pass")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == []
    assert function_def.return_type is None
    assert function_def.function_template == "def my_function():\n    pass"
    assert function_def.function_code == "def my_function():\n    pass"


# Visiting a function definition with default arguments
def test_function_with_default_arguments():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with default arguments
    code = ast.parse("def my_function(arg1, arg2='default', arg3=123):\n    pass")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == [
        ("arg1", "object"),
        ("arg2", "object"),
        ("arg3", "object"),
    ], f"{function_def.arg_types}"
    assert function_def.return_type is None
    assert (
        function_def.function_template
        == "def my_function(arg1, arg2='default', arg3=123):\n    pass"
    )
    assert (
        function_def.function_code
        == "def my_function(arg1, arg2='default', arg3=123):\n    pass"
    )


# Visiting a function definition with a decorator
def test_visiting_function_with_decorator():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with a decorator
    code = ast.parse("@decorator\ndef my_function():\n    pass")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == []
    assert function_def.return_type is None
    assert function_def.function_template == "@decorator\ndef my_function():\n    pass"
    assert function_def.function_code == "@decorator\ndef my_function():\n    pass"


# Visiting a class definition with no Pydantic inheritance
def test_visiting_class_definition_no_pydantic_inheritance():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a class definition with no Pydantic inheritance
    code = ast.parse(
        "class MyClass:\n    pass\n\n" "class MyOtherClass(BaseModel):\n    pass"
    )

    # Use pytest.raises to check if a ValidationError is raised
    # with pytest.raises(ValidationError):
    #     # Visit the AST
    visitor.visit(code)

    # class with no field is fine

    # Assert that the pydantic_classes list is empty
    assert len(get_pydantic_classes(visitor)) == 1


# Visiting a class definition with Pydantic inheritance
def test_visiting_class_with_pydantic_inheritance():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a class definition with Pydantic inheritance
    code = ast.parse("class MyClass(pydantic.BaseModel):\n    i: int")

    # Visit the AST
    visitor.visit(code)

    # Assert that the class name was added to the list of Pydantic classes
    assert "MyClass" in get_pydantic_classes(visitor)


# Visiting an import statement with an alias
def test_visiting_import_statement_with_alias():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for an import statement with an alias
    code = ast.parse("import module as m")

    # Visit the AST
    visitor.visit(code)

    # Assert that the import statement was added to the imports list
    assert "import module as m" in visitor.imports


# Visiting an import statement with no alias
def test_visiting_import_statement_with_no_alias():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for an import statement with no alias
    code = ast.parse("import module")

    # Visit the AST
    visitor.visit_Import(code.body[0])  # type: ignore

    # Assert that the import line was added to the imports list
    assert visitor.imports == ["import module"]


# Visiting a function definition with annotations that are not strings or constants
def test_visiting_function_with_non_string_annotations():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with non-string annotations
    code = ast.parse(
        "def my_function(arg1: int, arg2: List[str]) -> Dict[str, int]:\n    pass"
    )

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == [("arg1", "int"), ("arg2", "List[str]")]
    assert function_def.return_type == "Dict[str, int]"
    assert (
        function_def.function_template
        == "def my_function(arg1: int, arg2: List[str]) -> Dict[str, int]:\n    pass"
    )
    assert (
        function_def.function_code
        == "def my_function(arg1: int, arg2: List[str]) -> Dict[str, int]:\n    pass"
    )


# Visiting a function definition with a return annotation that is not a string or constant
def test_visiting_function_with_non_string_return_annotation():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with a non-string return annotation
    code = ast.parse("def my_function() -> int:\n    pass")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == []
    assert function_def.return_type == "int"
    assert function_def.function_template == "def my_function() -> int:\n    pass"
    assert function_def.function_code == "def my_function() -> int:\n    pass"


# Visiting a class definition with a body that is not a list of statements
def test_visiting_class_definition_with_non_list_body():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a class definition with a non-list body
    code = ast.parse("class MyClass:\n    x = 1")

    # Visit the AST
    visitor.visit(code)

    # Assert that the class was not added to the pydantic_classes list
    assert "MyClass" not in get_pydantic_classes(visitor)


# Visiting a function definition with a body that is not a list of statements
def test_visiting_function_with_non_list_body():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with a non-list body
    code = ast.parse("def my_function():\n    print('Hello, World!')")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == []
    assert function_def.return_type is None
    assert function_def.function_template == "def my_function():\n    pass"
    assert (
        function_def.function_code == "def my_function():\n    print('Hello, World!')"
    )


def test_visiting_function_with_pass_body():
    # Initialize FunctionVisitor
    visitor = FunctionVisitor()

    # Create AST for a function definition with a non-list body
    code = ast.parse("def my_function():\n    pass")

    # Visit the AST
    visitor.visit(code)
    functions = {f.name: f for f in visitor.functions}

    # Assert that the function was added to the functions dictionary
    assert "my_function" in functions

    # Assert the properties of the FunctionDef object
    function_def = functions["my_function"]
    assert function_def.name == "my_function"
    assert function_def.arg_types == []
    assert function_def.return_type is None
    assert not function_def.is_implemented


def get_pydantic_classes(visitor):
    return [c.name for c in visitor.objects if c.is_pydantic]
