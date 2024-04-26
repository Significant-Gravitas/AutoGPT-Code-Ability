import prisma
from prisma.models import Interview, InterviewStep

from codex.api_model import Identifiers
from codex.interview.model import UnderstandRequest


async def create_interview(ids: Identifiers, name: str, description: str) -> Interview:
    if not ids.user_id:
        raise AssertionError("User ID not found")
    if not ids.app_id:
        raise AssertionError("Application ID not found")
    interview = await prisma.models.Interview.prisma().create(
        data={
            "User": {"connect": {"id": ids.user_id}},
            "Application": {"connect": {"id": ids.app_id}},
            "name": name,
            "task": description,
        }
    )
    return interview


async def create_interview_steps(ids: Identifiers, ans: UnderstandRequest):
    await prisma.models.InterviewStep.prisma().create(
        data=prisma.types.InterviewStepCreateInput(
            Interview={"connect": {"id": ids.interview_id}},
            Application={"connect": {"id": ids.app_id}},
            phase_complete=ans.phase_completed,
            say=ans.say_to_user,
            thoughts=ans.thoughts,
            Features=prisma.types.FeatureCreateManyNestedWithoutRelationsInput(
                create=[
                    prisma.types.FeatureCreateWithoutRelationsInput(
                        name=f.name,
                        reasoning=f.reasoning,
                        functionality=f.functionality,
                    )
                    for f in ans.features or []
                ]
            ),
        )
    )


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
        ),
        order={
            "createdAt": "desc",
        },
    )
    return step
