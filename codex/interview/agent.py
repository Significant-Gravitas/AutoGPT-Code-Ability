# Task Breakdown Micro Agent
import logging

import prisma

from codex.common.ai_block import Identifiers
from codex.deploy.model import Application
from codex.interview.ai_interview import InterviewBlock
from codex.interview.model import InterviewResponse

logger = logging.getLogger(__name__)


async def start_interview(ids: Identifiers, app: Application) -> InterviewResponse:
    ai_block = InterviewBlock()

    ans = await ai_block.invoke(
        ids=ids,
        invoke_params={
            "product_name": app.name,
            "product_description": app.description,
        },
    )

    interview = await prisma.models.Interview.prisma().create(
        data={
            "User": {"connect": {"id": ids.user_id}},
            "Application": {"connect": {"id": ids.app_id}},
            "name": app.name,
            "task": app.description,
        }
    )

    await prisma.models.InterviewStep.prisma().create(
        data=prisma.types.InterviewStepCreateInput(
            Interview={"connect": {"id": interview.id}},
            Application={"connect": {"id": ids.app_id}},
            say=ans.say_to_user,
            thoughts=ans.thoughts,
            Features=prisma.types.FeatureCreateManyNestedWithoutRelationsInput(
                create=[
                    prisma.types.FeatureCreateWithoutRelationsInput(
                        name=f.name,
                        reasoning=f.reasoning,
                        functionality=f.functionality,
                    )
                    for f in ans.features
                ]
            ),
        )
    )

    return InterviewResponse(
        id=interview.id,
        say_to_user=ans.say_to_user,
        features=[f.name for f in ans.features],
        phase_completed=ans.phase_completed,
    )


async def continue_interview(
    ids: Identifiers, app: Application, user_message: str
) -> InterviewResponse:
    last_step = await prisma.models.InterviewStep.prisma().find_first_or_raise(
        where={
            "interviewId": ids.interview_id,
        },
        include={
            "Features": True,
        },
        order_by={
            "createdAt": prisma.SortOrder.desc,
        },
    )

    ai_block = InterviewBlock()
    features = "\n- ".join([f.name for f in last_step.Features])
    ans = await ai_block.invoke(
        ids=ids,
        invoke_params={
            "product_name": app.name,
            "product_description": app.description,
            "features": features,
            "user_msg": user_message,
        },
    )

    await prisma.models.InterviewStep.prisma().create(
        data=prisma.types.InterviewStepCreateInput(
            say=ans.say_to_user,
            thoughts=ans.thoughts,
            Interview={"connect": {"id": last_step.interviewId}},
            Features=[
                prisma.types.FeatureCreateInput(
                    name=f.name,
                    reasoning=f.reasoning,
                    functionality=f.functionality,
                )
                for f in ans.features
            ],
        )
    )

    return InterviewResponse(
        id=last_step.interviewId,
        say_to_user=ans.say_to_user,
        features=[f.name for f in ans.features],
        phase_completed=ans.phase_completed,
    )
