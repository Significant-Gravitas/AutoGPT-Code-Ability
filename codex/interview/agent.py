# Task Breakdown Micro Agent
import logging

import prisma
import prisma.models

from codex.common.ai_block import Identifiers
from codex.interview.ai_interview import InterviewBlock
from codex.interview.database import create_interview, create_interview_steps
from codex.interview.model import Feature, InterviewResponse, UnderstandRequest

logger = logging.getLogger(__name__)


async def start_interview(
    ids: Identifiers, app: prisma.models.Application
) -> InterviewResponse:
    ai_block = InterviewBlock()

    ans: UnderstandRequest = await ai_block.invoke(
        ids=ids,
        invoke_params={
            "product_name": app.name,
            "product_description": app.description,
        },
    )
    if not ids.user_id:
        raise AssertionError("User ID not found")
    if not ids.app_id:
        raise AssertionError("Application ID not found")
    if not app.description:
        raise AssertionError("Application description not found")

    interview = await create_interview(
        ids=ids,
        name=app.name,
        description=app.description,
    )
    ids.interview_id = interview.id

    await create_interview_steps(ids=ids, ans=ans)

    return InterviewResponse(
        id=interview.id,
        say_to_user=ans.say_to_user,
        features=[
            Feature(name=f.name, functionality=f.functionality)
            for f in ans.features or []
        ],
        phase_completed=ans.phase_completed,
    )


async def continue_interview(
    ids: Identifiers, app: prisma.models.Application, user_message: str
) -> InterviewResponse:
    try:
        if not ids.interview_id:
            raise AssertionError("Interview id not found")

        last_step = await prisma.models.InterviewStep.prisma().find_first_or_raise(
            where={
                "interviewId": ids.interview_id,
            },
            include={
                "Features": True,
            },
            order={
                "createdAt": "desc",
            },
        )

        ai_block = InterviewBlock()

        if not last_step.Features:
            raise AssertionError("Features not found in the last step")

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

        if ans.phase_completed:
            ans.features = last_step.Features

        await create_interview_steps(ids=ids, ans=ans)

        return InterviewResponse(
            id=last_step.interviewId,
            say_to_user=ans.say_to_user,
            features=[
                Feature(name=f.name, functionality=f.functionality)
                for f in ans.features
            ],
            phase_completed=ans.phase_completed,
        )
    except Exception:
        raise AssertionError("Error occured in inverview continue")
