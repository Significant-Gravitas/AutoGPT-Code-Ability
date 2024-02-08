import logging

from codex.requirements.database import create_spec
from codex.requirements.hardcoded import (
    appointment_optimization_requirements,
    availability_checker_requirements,
    distance_calculator_requirements,
    invoice_generator_requirements,
    profile_management,
)
from codex.requirements.model import ApplicationRequirements

logger = logging.getLogger(__name__)


def hardcoded_requirements(task: str) -> ApplicationRequirements:
    """
    This will take the application name and return the manually
    defined requirements for the application in the correct format
    """
    logger.warning("⚠️ Using hardcoded requirements")
    match task:
        case "Availability Checker":
            return availability_checker_requirements()
        case "Invoice Generator":
            return invoice_generator_requirements()
        case "Appointment Optimization Tool":
            return appointment_optimization_requirements()
        case "Distance Calculator":
            return distance_calculator_requirements()
        case "Profile Management System":
            return profile_management()
        case _:
            raise NotImplementedError(f"Task {task} not implemented")


async def populate_database():
    """
        This function will populate the database with the hardcoded requirements

         id |        createdAt        |        updatedAt        |             name              | deleted | userId
    ----+-------------------------+-------------------------+-------------------------------+---------+--------
      1 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Availability Checker          | f       |      1
      2 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Invoice Generator             | f       |      1
      3 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Appointment Optimization Tool | f       |      1
      4 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Distance Calculator           | f       |      1
      5 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Profile Management System     | f       |      1
      6 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Survey Tool                   | f       |      2
      7 | 2024-02-08 11:51:15.216 | 2024-02-08 11:51:15.216 | Scurvey Tool                  | t       |      2
    """
    import prisma

    from codex.api_model import Indentifiers

    db = prisma.Prisma(auto_register=True)
    requirmenets = [
        ("Availability Checker", 1),
        ("Invoice Generator", 1),
        ("Appointment Optimization Tool", 1),
        ("Distance Calculator", 1),
        ("Profile Management System", 1),
    ]
    await db.connect()
    ids = Indentifiers(user_id=1, app_id=1)

    for task, app_id in requirmenets:
        spec = hardcoded_requirements(task)
        ids.app_id = app_id
        await create_spec(ids, spec, db)
    await db.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(populate_database())
