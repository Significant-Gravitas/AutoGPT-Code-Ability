import prisma
from prisma.models import Interview, InterviewStep


async def delete_interview(interview_id: str) -> None:
    await Interview.prisma().update(
        where={"id": interview_id},
        data={"deleted": True},
    )


async def get_last_interview_step(interview_id: str, app_id: str) -> InterviewStep:
    step = await InterviewStep.prisma().find_first_or_raise(
        where=prisma.types.InterviewStepWhereInput(
            interviewId=interview_id, applicationId=app_id
        ),
        include=prisma.types.InterviewStepInclude(
            Features=True,
            Interview=True,
            Modules=True,
        ),
        order={
            "createdAt": "desc",
        },
    )
    return step
