# Task Breakdown Micro Agent
import logging

import prisma
import prisma.models

from codex.common.ai_block import Identifiers
from codex.interview.ai_interview import InterviewBlock
from codex.interview.ai_interview_update import InterviewUpdateBlock
from codex.interview.model import (
    Action,
    Feature,
    InterviewResponse,
    UpdateUnderstanding,
)

logger = logging.getLogger(__name__)


async def start_interview(
    ids: Identifiers, app: prisma.models.Application
) -> InterviewResponse:
    ai_block = InterviewBlock()

    ans = await ai_block.invoke(
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
                    for f in ans.features
                ]
            ),
        )
    )

    return InterviewResponse(
        id=interview.id,
        say_to_user=ans.say_to_user,
        features=[
            Feature(name=f.name, functionality=f.functionality) for f in ans.features
        ],
        phase_completed=ans.phase_completed,
    )


async def continue_interview(
    ids: Identifiers, app: prisma.models.Application, user_message: str
) -> InterviewResponse:
    """
    Apply feature updates to the given InterviewStep based on the provided UpdateUnderstanding.

    Args:
        last_step (prisma.models.InterviewStep): The last step of the interview to update.
        update (UpdateUnderstanding): The update containing information about the features to apply.

    Returns:
        list[prisma.types.FeatureCreateWithoutRelationsInput]: A list of updated features to be applied to the interview step.

    Raises:
        ValueError: If no features are found in the update or the last step.
        TypeError: If the features in the update are not in the expected list format.
    """

    try:
        if not ids.interview_id:
            raise AssertionError("Interview id not found")

        last_step: prisma.models.InterviewStep = (
            await prisma.models.InterviewStep.prisma().find_first_or_raise(
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
        )

        ai_block = InterviewUpdateBlock()

        if not last_step.Features:
            raise AssertionError("Features not found in the last step")

        features_prompt = InterviewUpdateBlock.create_feature_list(last_step.Features)

        ans = await ai_block.invoke(
            ids=ids,
            invoke_params={
                "product_name": app.name,
                "product_description": app.description,
                "features": features_prompt,
                "user_msg": user_message,
            },
        )

        features = apply_feature_updates(last_step, ans)

        await prisma.models.InterviewStep.prisma().create(
            data=prisma.types.InterviewStepCreateInput(
                phase_complete=ans.phase_completed,
                say=ans.say_to_user,
                thoughts=ans.thoughts,
                Interview={"connect": {"id": last_step.interviewId}},
                Application={"connect": {"id": ids.app_id}},
                Features=prisma.types.FeatureCreateManyNestedWithoutRelationsInput(
                    create=features
                ),
            )
        )

        return InterviewResponse(
            id=last_step.interviewId,
            say_to_user=ans.say_to_user,
            features=[
                Feature(name=f["name"], functionality=f["functionality"])
                for f in features
            ],
            phase_completed=ans.phase_completed,
        )
    except Exception as e:
        logger.exception(f"Error occurred during interview continuation: {e}")
        raise AssertionError(f"Error during interview continuation: {e}")


def apply_feature_updates(
    last_step: prisma.models.InterviewStep, update: UpdateUnderstanding
) -> list[prisma.types.FeatureCreateWithoutRelationsInput]:
    """
    Apply feature updates to the given InterviewStep based on the provided UpdateUnderstanding.

    Args:
        last_step (prisma.models.InterviewStep): The last step of the interview to update.
        update (UpdateUnderstanding): The update containing information about the features to apply.

    Returns:
        list[prisma.types.FeatureCreateWithoutRelationsInput]: A list of updated features to be applied to the interview step.

    Raises:
        ValueError: If no features are found in the update or the last step.
        TypeError: If the features in the update are not in the expected list format.
    """

    try:
        if update.features is None:
            raise ValueError("No features found in the update")
        if not isinstance(update.features, list):
            raise TypeError("Expected features to be a list")
        if not last_step.Features:
            raise ValueError("No features found in the last step")

        update_map = {f.id: f for f in update.features if f.action == Action.UPDATE}
        remove_set = {f.id for f in update.features if f.action == Action.REMOVE}

        new_feature_list = [
            prisma.types.FeatureCreateWithoutRelationsInput(
                name=f.name if f.name else "",
                reasoning=f.reasoning if f.reasoning else "",
                functionality=f.functionality if f.functionality else "",
            )
            for f in update.features
            if f.action == Action.ADD
        ]

        for i, f in enumerate(last_step.Features):
            if i in remove_set:
                continue
            updated_feature = update_map.get(i, f)
            new_feature_list.append(
                prisma.types.FeatureCreateWithoutRelationsInput(
                    name=updated_feature.name or f.name,
                    reasoning=updated_feature.reasoning or f.reasoning,
                    functionality=updated_feature.functionality or f.functionality,
                )
            )

        return new_feature_list
    except Exception as e:
        logger.exception(f"Error occured in apply_feature_updates: {e}")
        raise AssertionError(f"Error occured in apply_feature_updates: {e}")
