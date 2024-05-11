# Task Breakdown Micro Agent
import logging

import prisma
import prisma.enums
import prisma.models
from langsmith import traceable

import codex.interview.model
from codex.common.ai_block import Identifiers
from codex.interview.ai_interview import InterviewBlock
from codex.interview.ai_interview_update import InterviewUpdateBlock
from codex.interview.ai_module import ModuleGenerationBlock
from codex.interview.model import Action, InterviewResponse, UpdateUnderstanding

logger = logging.getLogger(__name__)


@traceable
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

    response_string = ans.say_to_user
    response_string += "\n\n## Features:\n"
    for feature in ans.features:
        response_string += f"- **{feature.name}** - {feature.functionality}\n"
    response_string += "\nAre there any changes you would like to make or are you ready to move onto designing the app together?"

    return InterviewResponse(
        id=interview.id,
        say_to_user=response_string,
        phase=prisma.enums.InterviewPhase.FEATURES.value,
        phase_completed=False,
    )


@traceable
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
                    "Modules": True,
                },
                order={
                    "createdAt": "desc",
                },
            )
        )
        # We update the phase based on the last step
        phase = last_step.phase
        if last_step.phase_complete:
            if last_step.phase == prisma.enums.InterviewPhase.FEATURES:
                phase = prisma.enums.InterviewPhase.ARCHITECT
            elif last_step.phase == prisma.enums.InterviewPhase.ARCHITECT:
                phase = prisma.enums.InterviewPhase.COMPLETED
            else:
                raise ValueError("Invalid phase transition")

        if phase == prisma.enums.InterviewPhase.FEATURES:
            return await continue_feature_phase(ids, app, user_message, last_step)
        elif phase == prisma.enums.InterviewPhase.ARCHITECT:
            return await continue_architect_phase(ids, app, user_message, last_step)
        elif phase == prisma.enums.InterviewPhase.COMPLETED:
            return InterviewResponse(
                id=ids.interview_id,
                say_to_user="The interview is already completed",
                phase=prisma.enums.InterviewPhase.COMPLETED.value,
                phase_completed=True,
            )
    except Exception as e:
        logger.exception(f"Error occurred during interview continuation: {e}")
        raise AssertionError(f"Error during interview continuation: {e}")

    # Add a return statement to ensure that the function always returns an InterviewResponse
    return InterviewResponse(
        id=ids.interview_id,
        say_to_user="An Unknown error occurred during interview continuation",
        phase=prisma.enums.InterviewPhase.FEATURES.value,
        phase_completed=False,
    )


async def continue_feature_phase(
    ids: Identifiers,
    app: prisma.models.Application,
    user_message: str,
    last_step: prisma.models.InterviewStep,
) -> InterviewResponse:
    try:
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
                phase=prisma.enums.InterviewPhase.FEATURES,
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

        response_string = ans.say_to_user
        if not ans.phase_completed:
            response_string += "\n\n## Features:\n"
            for feature in features:
                response_string += (
                    f"- **{feature['name']}** - {feature['functionality']}\n"
                )
            response_string += "\nAre there any changes you would like to make or are you ready to move onto designing the app together?"

        return InterviewResponse(
            id=last_step.interviewId,
            say_to_user=response_string,
            phase=prisma.enums.InterviewPhase.FEATURES.value,
            phase_completed=ans.phase_completed,
        )
    except Exception as e:
        logger.exception(f"Error occurred during interview features continuation: {e}")
        raise AssertionError(f"Error during interview features continuation: {e}")


async def continue_architect_phase(
    ids: Identifiers,
    app: prisma.models.Application,
    user_message: str,
    last_step: prisma.models.InterviewStep,
) -> InterviewResponse:
    try:
        if not last_step.Features:
            raise AssertionError("Features not found in the last step")

        features_string = ""
        for feature in last_step.Features:
            features_string += "\nFeature Name: " + str(feature.name)
            features_string += "\nFunctionality: " + str(feature.functionality)
            features_string += "\nReasoning: " + str(feature.reasoning)
            features_string += "\n"

        logger.info("Defining Modules from features")

        module_block = ModuleGenerationBlock()

        invoke_params = {
            "product_name": app.name,
            "product_description": app.description,
            "features": features_string,
        }
        if last_step.Modules:
            invoke_params["modules"] = ModuleGenerationBlock.create_modules_list(
                last_step.Modules
            )

        if user_message:
            invoke_params["user_msg"] = user_message

        module_response: codex.interview.model.ModuleResponse = (
            await module_block.invoke(
                ids=ids,
                invoke_params=invoke_params,
            )
        )

        say_to_user = module_response.say_to_user + "\n\n## Modules:\n"

        logger.info(f"Say to user raw: {module_response.say_to_user}")

        latest_modules = apply_module_update(last_step, module_response)
        last_step_num_modules = len(last_step.Modules) if last_step.Modules else 0
        module_response_num_modules = (
            len(module_response.modules) if module_response.modules else 0
        )
        latest_modules_num_modules = len(latest_modules) if latest_modules else 0
        logger.info(
            f"Number of modules in last step: {last_step_num_modules}, Number of modules in module response: {module_response_num_modules}, Number of latest modules: {latest_modules_num_modules}"
        )
        if latest_modules:
            for module in latest_modules:
                say_to_user += f"- **{module['name']}** - {module['description']}\n"

        say_to_user += "\nAre there any changes you would like to make or are you ready for me to develop the app?"

        logger.info(f"Say to user: {say_to_user}")

        await prisma.models.InterviewStep.prisma().create(
            data=prisma.types.InterviewStepCreateInput(
                phase=prisma.enums.InterviewPhase.ARCHITECT,
                phase_complete=module_response.phase_completed,
                say=say_to_user,
                thoughts=module_response.thoughts,
                Interview={"connect": {"id": last_step.interviewId}},
                Application={"connect": {"id": ids.app_id}},
                Features=prisma.types.FeatureCreateManyNestedWithoutRelationsInput(
                    create=[
                        prisma.types.FeatureCreateWithoutRelationsInput(
                            name=f.name,
                            reasoning=f.reasoning,
                            functionality=f.functionality,
                        )
                        for f in last_step.Features
                    ]
                ),
                Modules=prisma.types.ModuleCreateManyNestedWithoutRelationsInput(
                    create=latest_modules
                ),
                access_roles=module_response.access_roles
                if module_response.access_roles
                else [],
            )
        )

        return InterviewResponse(
            id=last_step.interviewId,
            say_to_user=say_to_user,
            phase=prisma.enums.InterviewPhase.ARCHITECT.value,
            phase_completed=module_response.phase_completed,
        )
    except Exception as e:
        logger.exception(f"Error occurred during interview modules continuation: {e}")
        raise AssertionError(f"Error during interview modules continuation: {e}")


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
        if not last_step.Features:
            raise ValueError("No features found in the last step")

        # If features is None or an empty list, return the existing features
        if not update.features:
            return [
                prisma.types.FeatureCreateWithoutRelationsInput(
                    name=f.name,
                    reasoning=f.reasoning,
                    functionality=f.functionality,
                )
                for f in last_step.Features
            ]

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
            if i in update_map:
                updated_feature = update_map[i]
                new_feature_list.append(
                    prisma.types.FeatureCreateWithoutRelationsInput(
                        name=updated_feature.name if updated_feature.name else f.name,
                        reasoning=updated_feature.reasoning
                        if updated_feature.reasoning
                        else f.reasoning,
                        functionality=updated_feature.functionality
                        if updated_feature.functionality
                        else f.functionality,
                    )
                )
            else:
                new_feature_list.append(
                    prisma.types.FeatureCreateWithoutRelationsInput(
                        name=f.name,
                        reasoning=f.reasoning,
                        functionality=f.functionality,
                    )
                )

        return new_feature_list
    except Exception as e:
        logger.exception(f"Error occured in apply_feature_updates: {e}")
        raise RuntimeError(f"Error occured in apply_feature_updates: {e}")


def apply_module_update(
    last_step: prisma.models.InterviewStep, update: codex.interview.model.ModuleResponse
) -> list[prisma.types.ModuleCreateWithoutRelationsInput]:
    if not last_step.Modules and not update.modules:
        raise ValueError("No modules found in the last step or the update")

    if not update.modules and last_step.Modules:
        return [
            prisma.types.ModuleCreateWithoutRelationsInput(
                name=module.name,
                description=module.description,
                interactions=module.interactions,
            )
            for module in last_step.Modules
        ]

    assert update.modules, "No modules found in the update"

    update_map = {m.id: m for m in update.modules if m.action == Action.UPDATE}
    remove_set = {m.id for m in update.modules if m.action == Action.REMOVE}

    new_module_list = [
        prisma.types.ModuleCreateWithoutRelationsInput(
            name=m.name if m.name else "",
            description=m.functionality if m.functionality else "",
            interactions="\n".join(m.interaction_with_other_modules)
            if m.interaction_with_other_modules
            else "",
        )
        for m in update.modules
        if m.action == Action.ADD
    ]
    if not last_step.Modules:
        return new_module_list

    for i, m in enumerate(last_step.Modules):
        if i in remove_set:
            continue
        if i in update_map:
            updated_module = update_map[i]
            new_module_list.append(
                prisma.types.ModuleCreateWithoutRelationsInput(
                    name=updated_module.name if updated_module.name else m.name,
                    description=updated_module.functionality
                    if updated_module.functionality
                    else m.description,
                    interactions="\n".join(
                        updated_module.interaction_with_other_modules
                    )
                    if updated_module.interaction_with_other_modules
                    else m.interactions,
                )
            )
        else:
            # Add in the modules that are not to be changed
            new_module_list.append(
                prisma.types.ModuleCreateWithoutRelationsInput(
                    name=m.name,
                    description=m.description,
                    interactions=m.interactions,
                )
            )

    return new_module_list
