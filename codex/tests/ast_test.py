import ast

import pytest

from codex.develop.develop import FunctionVisitor

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

    # Check that all Pydantic classes are identified
    assert "SomeClass" not in visitor.pydantic_classes
    assert "ProfessionalWorkingHours" in visitor.pydantic_classes

    # Check that all functions are identified
    assert len(visitor.pydantic_classes) == 4
    assert len(visitor.functions) == 3
