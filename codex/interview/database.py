from prisma.models import Interview


async def delete_interview(interview_id: str) -> None:
    await Interview.prisma().update(
        where={"id": interview_id},
        data={"deleted": True},
    )
