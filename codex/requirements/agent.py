import asyncio
import json
import logging
from asyncio import run

import prisma
from prisma.enums import AccessLevel
from prisma.models import Specification
from pydantic.json import pydantic_encoder

from codex.api_model import Identifiers
from codex.common.ai_model import OpenAIChatClient
from codex.common.logging_config import setup_logging
from codex.common.model import ObjectFieldModel
from codex.common.model import ObjectTypeModel as ObjectTypeE
from codex.common.test_const import identifier_1
from codex.interview.database import get_interview
from codex.prompts.claude.requirements.NestJSDocs import (
    NEST_JS_CRUD_GEN,
    NEST_JS_FIRST_STEPS,
    NEST_JS_MODULES,
    NEST_JS_SQL,
)
from codex.requirements import flatten_endpoints
from codex.requirements.blocks.ai_clarify import (
    FrontendClarificationBlock,
    QuestionAndAnswerClarificationBlock,
    UserPersonaClarificationBlock,
    UserSkillClarificationBlock,
)
from codex.requirements.blocks.ai_database import DatabaseGenerationBlock
from codex.requirements.blocks.ai_endpoint import EndpointSchemaRefinementBlock
from codex.requirements.blocks.ai_feature import FeatureGenerationBlock
from codex.requirements.blocks.ai_module import (
    ModuleGenerationBlock,
    ModuleRefinementBlock,
)
from codex.requirements.blocks.ai_requirements import (
    BaseRequirementsBlock,
    FuncNonFuncRequirementsBlock,
)
from codex.requirements.database import create_spec
from codex.requirements.matching import find_best_match
from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    Clarification,
    DBResponse,
    Feature,
    FeaturesSuperObject,
    Module,
    ModuleRefinement,
    ModuleResponse,
    QandA,
    RequirementsGenResponse,
    RequirementsRefined,
    StateObj,
)
from codex.requirements.unwrap_schemas import convert_endpoint

logger = logging.getLogger(__name__)


async def generate_requirements(ids: Identifiers, description: str) -> Specification:
    """
    Runs the Requirements Agent to generate the system requirements based
    upon the provided task

    Args:
        ids (Identifiers): Relevant ids for database operations
        description (str): description of the application

    Returns:
        ApplicationRequirements: The system requirements for the application
    """
    if not ids.user_id or not ids.app_id:
        raise ValueError("User and App Ids are required")

    running_state_obj = StateObj(task=description)

    logger.info("State Object Created")

    # User Interview
    interview = await get_interview(
        user_id=ids.user_id, app_id=ids.app_id, interview_id=ids.interview_id or ""
    )

    if not interview:
        raise ValueError("Interview not found")

    questions = interview.Questions or []
    running_state_obj.project_description = [
        question for question in questions if question.tool == "finished"
    ][0].question
    running_state_obj.project_description_thoughts = "\n".join(
        [f"{item.tool}: {item.question} :{item.answer}" for item in questions]
    )

    logger.info("User Interview Done")

    frontend_clarify = FrontendClarificationBlock()
    frontend_clarification: Clarification = await frontend_clarify.invoke(
        ids=ids,
        invoke_params={"project_description": running_state_obj.project_description},
    )

    running_state_obj.add_clarifying_question(frontend_clarification)

    logger.info("Frontend Clarification Done")

    user_persona_clarify = UserPersonaClarificationBlock()
    user_persona_clarification: Clarification = await user_persona_clarify.invoke(
        ids=ids,
        invoke_params={
            "clarifiying_questions_so_far": running_state_obj.clarifying_questions_as_string(),
            "project_description": running_state_obj.project_description,
        },
    )

    running_state_obj.add_clarifying_question(user_persona_clarification)

    logger.info("User Persona Clarification Done")

    # User Skill

    user_skill_clarify = UserSkillClarificationBlock()
    user_skill_clarification: Clarification = await user_skill_clarify.invoke(
        ids=ids,
        invoke_params={
            "clarifiying_questions_so_far": running_state_obj.clarifying_questions_as_string(),
            "project_description": running_state_obj.project_description,
        },
    )
    running_state_obj.add_clarifying_question(user_skill_clarification)

    logger.info("User Skill Clarification Done")

    # Clarification Rounds

    q_and_a_clarify = QuestionAndAnswerClarificationBlock()
    q_and_a_clarification: list[QandA] = await q_and_a_clarify.invoke(
        ids=ids,
        invoke_params={
            "clarifiying_questions_so_far": running_state_obj.clarifying_questions_as_string(),
            "project_description": running_state_obj.project_description,
            "task": running_state_obj.task,
        },
    )

    running_state_obj.q_and_a = q_and_a_clarification

    logger.info("Question and Answer Based Clarification Done")

    # Product Name and Description
    feature_block = FeatureGenerationBlock()
    feature_so: FeaturesSuperObject = await feature_block.invoke(
        ids=ids,
        invoke_params={
            "project_description": running_state_obj.project_description,
            "project_description_thoughts": running_state_obj.project_description_thoughts,
            "joint_q_and_a": running_state_obj.joint_q_and_a(),
        },
    )

    # Parsing
    running_state_obj.product_name = interview.name
    running_state_obj.product_description = feature_so.description
    features: list[Feature] = []

    for feature in feature_so.features:
        features.append(feature.feature)

    running_state_obj.features = features

    logger.info("Features Done")

    # Requirements Start
    # Collect the requirements Q&A
    base_requirements_block = BaseRequirementsBlock()
    base_requirements: RequirementsRefined = await base_requirements_block.invoke(
        ids=ids,
        invoke_params={
            "project_description": running_state_obj.project_description,
            "project_description_thoughts": running_state_obj.project_description_thoughts,
            "joint_q_and_a": running_state_obj.joint_q_and_a(),
        },
    )

    running_state_obj.requirements_q_and_a = base_requirements.dirty_requirements or []

    running_state_obj.refined_requirement_q_a = base_requirements

    logger.info("Refined Requirements Done")

    # Requirements QA answers
    # Build the requirements from the Q&A
    requirements_func_nonfunc_block = FuncNonFuncRequirementsBlock()
    requirements_func_nonfunc: RequirementsGenResponse = (
        await requirements_func_nonfunc_block.invoke(
            ids=ids,
            invoke_params={
                "product_description": running_state_obj.product_description,
                "joint_q_and_a": running_state_obj.joint_q_and_a(),
                "requirements_q_and_a": running_state_obj.requirements_q_and_a_string(),
                "features": json.dumps(
                    running_state_obj.features, default=pydantic_encoder
                ),
            },
        )
    )

    running_state_obj.requirements = requirements_func_nonfunc.answer

    logger.info("Requirements Done")

    # Modules seperation
    # Build the requirements from the Q&A
    module_block = ModuleGenerationBlock()
    module_response: ModuleResponse = await module_block.invoke(
        ids=ids,
        invoke_params={
            "NEST_JS_FIRST_STEPS": NEST_JS_FIRST_STEPS,
            "NEST_JS_MODULES": NEST_JS_MODULES,
            "NEST_JS_SQL": NEST_JS_SQL,
            "NEST_JS_CRUD_GEN": NEST_JS_CRUD_GEN,
            "product_description": running_state_obj.product_description,
            "requirements_q_and_a": running_state_obj.requirements_q_and_a_string(),
            "requirements": json.dumps(
                running_state_obj.requirements, default=pydantic_encoder
            ),
            "joint_q_and_a": running_state_obj.joint_q_and_a(),
            "features": json.dumps(
                running_state_obj.features, default=pydantic_encoder
            ),
        },
    )

    running_state_obj.modules = module_response.modules

    logger.info("Modules 1st Step Done")

    # Database Generation
    if running_state_obj.refined_requirement_q_a.need_db:
        logger.info("DB Started")
        # Database Design
        database_block = DatabaseGenerationBlock()

        db_invoke_params = {
            "product_spec": running_state_obj.__str__(),
            "needed_auth_roles": running_state_obj.refined_requirement_q_a.authorization_roles,
            "modules": ", ".join(module.name for module in running_state_obj.modules),
        }

        db_response: DBResponse = await database_block.invoke(
            ids=ids,
            invoke_params=db_invoke_params,
        )

        running_state_obj.database = db_response.database_schema

        logger.info("DB Done")

    # Module Refinement
    # Build the requirements from the Q&A
    module_ref_block = ModuleRefinementBlock()
    refined_data: ModuleRefinement = await module_ref_block.invoke(
        ids=ids,
        invoke_params={
            "system_requirements": running_state_obj.__str__(),
            "modules_list": ", ".join(
                [module.name for module in running_state_obj.modules]
            ),
        },
    )

    logger.info("Refined Modules Generated Done")

    # Match modules to completions
    for module in refined_data.modules:
        # Extract module names from running_state_obj.modules for comparison
        existing_module_names = [
            existing.name for existing in running_state_obj.modules
        ]
        # Find the best match for module.module_name in existing_module_names
        match = find_best_match(module.module_name, existing_module_names, threshold=80)

        if match:
            best_match, _similarity = match[0], match[1]
            # If a good match is found, proceed to update the module details
            for index, existing in enumerate(running_state_obj.modules):
                if existing.name == best_match:
                    logger.debug(f"Matched a module {existing.name}")
                    running_state_obj.modules[
                        index
                    ].description = module.new_description
                    endpoints = flatten_endpoints.flatten_endpoints(
                        module.endpoint_groups
                    )
                    running_state_obj.modules[index].endpoints = endpoints
                    requirements = [
                        requirement for requirement in module.module_requirements
                    ]
                    running_state_obj.modules[index].requirements = requirements
        else:
            logger.error(f"No close match found for {module.module_name}")

    logger.info("Refined Modules Done")

    # DB Schemas
    db_table_names: list[str] = []
    if running_state_obj.database:
        db_table_names = [
            table.name or "" for table in running_state_obj.database.tables
        ]

    # DB Enums
    db_enum_names: list[str] = []
    if running_state_obj.database:
        db_enum_names = [enum.name or "" for enum in running_state_obj.database.enums]

    # This process just refineds the api endpoints. It can be ran in parallel
    # for all the modules and their endpoints
    async def process_module(
        module: Module, running_state_obj: StateObj, db_table_names: list[str]
    ):
        if module.endpoints:
            logger.info(f"Endpoints for {module.name} Started")

            endpoint_block = EndpointSchemaRefinementBlock()
            new_endpoints = await asyncio.gather(
                *[
                    endpoint_block.invoke(
                        ids=ids,
                        invoke_params={
                            "spec": running_state_obj.__str__(),
                            "db_models": f"[{','.join(db_table_names)}]",
                            "db_enums": f"[{','.join(db_enum_names)}]",
                            "module_repr": f"{module!r}",
                            "endpoint_repr": f"{endpoint!r}",
                        },
                    )
                    for endpoint in module.endpoints
                ]
            )

            for j, new_endpoint in enumerate(new_endpoints):
                converted = convert_endpoint(
                    input=new_endpoint,
                    existing=module.endpoints[j],
                    database=running_state_obj.database,
                )
                logger.debug(f"{converted!r}")
                logger.info(f"Endpoint {converted.type} {converted.name} Done")
                module.endpoints[j] = converted
            logger.info(f"Endpoints for {module.name} Done")

    # Gather all module processing tasks
    module_tasks = [
        process_module(module, running_state_obj, db_table_names)
        for module in running_state_obj.modules
    ]

    # Run all module tasks in parallel
    await asyncio.gather(*module_tasks)

    logger.info("Endpoints Done")

    api_routes: list[APIRouteRequirement] = []
    for module in running_state_obj.modules:
        if module.endpoints:
            for route in module.endpoints:
                logger.debug(route)
                logger.info(f"Processing route {route.name}")
                api_routes.append(
                    APIRouteRequirement(
                        function_name=route.name,
                        method=route.type,
                        path=route.path,
                        description=route.description,
                        request_model=route.request_model
                        or ObjectTypeE(name="None", Fields=[]),
                        response_model=route.response_model
                        or ObjectTypeE(
                            name="Output",
                            Fields=[
                                ObjectFieldModel(
                                    name="message",
                                    type="str",
                                    description="The message returned by the route",
                                ),
                                ObjectFieldModel(
                                    name="status_code",
                                    type="int",
                                    description="The status returned by the route",
                                ),
                            ],
                        ),
                        database_schema=route.database_schema,
                        access_level=AccessLevel.PUBLIC,
                    )
                )

    full_spec = ApplicationRequirements(
        name=running_state_obj.product_name,
        context=running_state_obj.project_description,
        api_routes=api_routes,
    )
    logger.info("Full Spec Done")
    saved_spec: Specification = await create_spec(ids, full_spec)
    logger.info("Saved Spec Done")
    if logger.level == logging.DEBUG:
        with open("requirements_debug.py", "a+") as f:
            f.write(f"# Name: {running_state_obj.product_name}\n")
            f.write(f"full_spec = {full_spec!r}\n")
            f.write(f"saved_spec = {saved_spec!r}\n")
            f.write("\n")
            f.write("\n")
    # Step 8) Return the application requirements
    return saved_spec


if __name__ == "__main__":
    from codex.common.test_const import interview_id_1

    ids = identifier_1
    db_client = prisma.Prisma(auto_register=True)

    OpenAIChatClient.configure({})
    task = """The Tutor App is an app designed for tutors to manage their clients,
 schedules, and invoices.

It must support both the client and tutor scheduling, rescheduling and canceling
 appointments, and sending invoices after the appointment has passed.

Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign
 up with traditional authentication, it must be safe and secure. There will need to be
 password reset and login capabilities.

There will need to be authorization for identifying clients vs the tutor.

Additionally, it will have proper management of financials, including invoice management
 and payment tracking. This includes things like paid/failed invoice notifications,
 unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."""

    async def run_gen():
        await db_client.connect()
        ids.interview_id = interview_id_1
        setup_logging(local=True)
        logger.info("Starting Requirements Generation")
        output = await generate_requirements(ids=ids, description=task)
        logger.info("Requirements Generation Done")
        return output

    out = run(run_gen())
    logger.info(out)
