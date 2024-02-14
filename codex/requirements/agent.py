from asyncio import run
import logging

import openai
import prisma
from prisma.enums import AccessLevel

from codex.common.ai_block import Indentifiers
from codex.requirements import flatten_endpoints
from codex.requirements.ai_clarify import (
    FrontendClarificationBlock,
    QuestionAndAnswerClarificationBlock,
    UserPersonaClarificationBlock,
    UserSkillClarificationBlock,
)
from codex.requirements.ai_feature import FeatureGenerationBlock
from codex.requirements.complete import complete_and_parse, complete_anth
from codex.requirements.database import create_spec
from codex.requirements.gather_task_info import gather_task_info_loop
from codex.requirements.hardcoded import (
    appointment_optimization_requirements,
    availability_checker_requirements,
    distance_calculator_requirements,
    invoice_generator_requirements,
    profile_management,
)
from codex.requirements.matching import find_best_match
from codex.requirements.model import (
    APIRouteRequirement,
    ApplicationRequirements,
    Clarification,
    DBResponse,
    Endpoint,
    EndpointSchemaRefinementResponse,
    Feature,
    FeaturesSuperObject,
    ModuleRefinement,
    ModuleResponse,
    QandA,
    QandAResponses,
    RequestModel,
    RequirementsGenResponse,
    RequirementsResponse,
    ResponseModel,
    StateObj,
)

from codex.prompts.claude.requirements.ClarificationsIntoProduct import *
from codex.prompts.claude.requirements.ProductIntoRequirement import *
from codex.prompts.claude.requirements.RequirementIntoModule import *
from codex.prompts.claude.requirements.TaskIntoClarifcations import *
from codex.prompts.claude.requirements.ModuleRefinement import *
from codex.prompts.claude.requirements.ModuleIntoDatabase import *
from codex.prompts.claude.requirements.EndpointGeneration import *
from codex.prompts.claude.requirements.AskFunction import *
from codex.prompts.claude.requirements.QAFormat import *
from codex.prompts.claude.requirements.SearchFunction import *
from codex.requirements.build_requirements_refinement_object import (
    convert_requirements,
    RequirementsRefined,
)
from codex.requirements.parser import parse
from codex.requirements.unwrap_schemas import (
    convert_endpoint,
    unwrap_db_schema,
)

logger = logging.getLogger(__name__)


async def generate_requirements(
    ids: Indentifiers,
    app_name: str,
    description: str,
) -> ApplicationRequirements:
    """
    Runs the Requirements Agent to generate the system requirements based
    upon the provided task

    Args:
        ids (Indentifiers): Relevant ids for database operations
        app_name (str): name of the application
        description (str): description of the application

    Returns:
        ApplicationRequirements: The system requirements for the application
    """

    running_state_obj = StateObj(task=description)

    # User Interview
    full, completion = gather_task_info_loop(running_state_obj.task, ask_callback=None)
    running_state_obj.project_description = completion.split("finished: ")[-1].strip()
    running_state_obj.project_description_thoughts = full

    print(running_state_obj.project_description_thoughts)

    frontend_clarify = FrontendClarificationBlock()
    frontend_clarification: Clarification = await frontend_clarify.invoke(
        ids=ids,
        invoke_params={"project_description": running_state_obj.project_description},
    )

    running_state_obj.add_clarifying_question(frontend_clarification)

    print("Frontend Clarification Done")

    user_persona_clarify = UserPersonaClarificationBlock()
    user_persona_clarification: Clarification = await user_persona_clarify.invoke(
        ids=ids,
        invoke_params={
            "clarifiying_questions_so_far": running_state_obj.clarifying_questions_as_string(),
            "project_description": running_state_obj.project_description,
        },
    )

    running_state_obj.add_clarifying_question(user_persona_clarification)

    print("User Persona Clarification Done")

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

    print("User Skill Clarification Done")

    # Clarification Rounds

    q_and_a_clarify = QuestionAndAnswerClarificationBlock()
    q_and_a_clarification: list[QandA] = await q_and_a_clarify.invoke(
        ids=ids,
        invoke_params={
            "clarifiying_questions_so_far": running_state_obj.clarifying_questions_as_string(),
            "project_description": running_state_obj.project_description,
            "task": task,
        },
    )

    running_state_obj.q_and_a = q_and_a_clarification

    print("Question and Answer Based Clarification Done")

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
    running_state_obj.product_name = feature_so.project_name
    running_state_obj.product_description = feature_so.description
    features: list[Feature] = []

    for feature in feature_so.features:
        features.append(feature.feature)

    running_state_obj.features = features

    print("Features Done")

    # Requirements Start
    # Collect the requirements Q&A
    requirement_response: RequirementsResponse = complete_and_parse(
        prompt=FEATURE_BASELINE_CHECKS.format(
            joint_q_and_a=running_state_obj.joint_q_and_a(),
            product_description=running_state_obj.product_description,
            FEATURE_BASELINE_QUESTIONS=FEATURE_BASELINE_QUESTIONS,
            features=str([feature.dict() for feature in running_state_obj.features]),
        ),
        return_model=RequirementsResponse,
    )
    running_state_obj.requirements_q_and_a = [
        requirement.wrapper for requirement in requirement_response.answer
    ]

    # Requirements conversion
    refined_requirements = convert_requirements(running_state_obj.requirements_q_and_a)
    running_state_obj.refined_requirement_q_a = refined_requirements

    print("Refined Requirements Done")

    # Requirements QA answers
    # Build the requirements from the Q&A
    requirement_gen_response: RequirementsGenResponse = complete_and_parse(
        prompt=REQUIREMENTS.format(
            joint_q_and_a=running_state_obj.joint_q_and_a(),
            product_description=running_state_obj.product_description,
            FEATURE_BASELINE_QUESTIONS=FEATURE_BASELINE_QUESTIONS,
            features=str([feature.dict() for feature in running_state_obj.features]),
            requirements_q_and_a_string=running_state_obj.requirements_q_and_a_string(),
        ),
        return_model=RequirementsGenResponse,
    )
    print(requirement_gen_response)
    running_state_obj.requirements = requirement_gen_response.answer

    print("Requirements Done")

    # Modules seperation
    # Build the requirements from the Q&A
    module_response: ModuleResponse = complete_and_parse(
        prompt=REQUIREMENTS_INTO_MODULES.format(
            NEST_JS_FIRST_STEPS=NEST_JS_FIRST_STEPS,
            NEST_JS_MODULES=NEST_JS_MODULES,
            NEST_JS_SQL=NEST_JS_SQL,
            NEST_JS_CRUD_GEN=NEST_JS_CRUD_GEN,
            product_description=running_state_obj.product_description,
            requirements_q_and_a_string=running_state_obj.requirements_q_and_a_string(),
            requirements=str(running_state_obj.requirements),
            joint_q_and_a=running_state_obj.joint_q_and_a(),
            features=str([feature.dict() for feature in running_state_obj.features]),
        ),
        return_model=ModuleResponse,
    )
    running_state_obj.modules = [x.module for x in module_response.answer]

    print("Modules 1st Step Done")

    # Database Design
    running_state_obj.database = None
    db_response: DBResponse = complete_and_parse(
        MODULE_INTO_INTO_DATABASE.format(
            product_spec=running_state_obj.__str__(),
            needed_auth_roles=running_state_obj.refined_requirement_q_a.authorization_roles,
            modules={", ".join(module.name for module in running_state_obj.modules)},
        ),
        return_model=DBResponse,
    )
    running_state_obj.database = unwrap_db_schema(db_response.database_schema)

    print("DB Done")

    # Module Refinement
    # Build the requirements from the Q&A
    refined_data: ModuleRefinement = complete_and_parse(
        prompt=MODULE_REFINEMENTS.format(
            system_requirements=f"{running_state_obj.__str__()}", id=f"{id}"
        ),
        return_model=ModuleRefinement,
    )

    print("Refined Modules Generated Done")

    # Match modules to completions
    for module in refined_data.modules:
        module = module.module
        # Extract module names from running_state_obj.modules for comparison
        existing_module_names = [
            existing.name for existing in running_state_obj.modules
        ]
        # Find the best match for module.module_name in existing_module_names
        match = find_best_match(module.module_name, existing_module_names, threshold=80)

        if match:
            best_match, similarity = match[0], match[1]
            # If a good match is found, proceed to update the module details
            for index, existing in enumerate(running_state_obj.modules):
                if existing.name == best_match:
                    print(existing.name)
                    running_state_obj.modules[
                        index
                    ].description = module.new_description
                    endpoints = flatten_endpoints.flatten_endpoints(module.endpoints)
                    running_state_obj.modules[index].endpoints = endpoints
                    requirements = [
                        requirement.requirement
                        for requirement in module.module_requirements_list
                    ]
                    running_state_obj.modules[index].requirements = requirements
        else:
            print(f"No close match found for {module.module_name}")

    print("Refined Modules Done")

    # DB Schemas
    reply = ""
    db_table_names: list[str] = [
        table.name or "" for table in running_state_obj.database.tables
    ]
    for i, module in enumerate(running_state_obj.modules):
        if module.endpoints:
            for j, endpoint in enumerate(module.endpoints):
                reply = complete_and_parse(
                    ENDPOINT_PARAMS_GEN.format(
                        endpoint_and_module_repr=f"{endpoint!r} {module!r}",
                        spec=running_state_obj.__str__(),
                        id="{id}",
                        db_models=f"[{','.join(db_table_names)}]",
                    ),
                    return_model=EndpointSchemaRefinementResponse,
                )
                # parsed = parse_into_model(reply, EndpointSchemaRefinementResponse)
                # display(Pretty(parsed.__str__()))
                converted: Endpoint = convert_endpoint(
                    input=reply,
                    existing=endpoint,
                    database=running_state_obj.database,
                )
                running_state_obj.modules[i].endpoints[j] = converted

    print("Endpoints Done")

    # Add support and tracking for models by module and add them to the prompt

    # Step 5) Define the request and response models

    # We maybe able to avoid needing llm calls for that

    # Step 6) Generate the complete api route requirements

    # Step 7) Compile the application requirements

    api_routes: list[APIRouteRequirement] = []
    for module in running_state_obj.modules:
        if module.endpoints:
            for route in module.endpoints:
                print(route)
                api_routes.append(
                    APIRouteRequirement(
                        function_name=route.name,
                        method=route.type,
                        path=route.path,
                        description=route.description,
                        request_model=route.request_model
                        or RequestModel(
                            name="None Provided",
                            description="None Proviced",
                            params=[],
                        ),
                        response_model=route.response_model
                        or ResponseModel(
                            name="None Provided",
                            description="None Proviced",
                            params=[],
                        ),
                        database_schema=route.database_schema,
                        access_level=AccessLevel.PUBLIC,
                        data_models=route.data_models,
                    )
                )

    full_spec = ApplicationRequirements(
        name=running_state_obj.product_name,
        context=running_state_obj.__str__(),
        api_routes=api_routes,
    )
    # saved_spec = await create_spec(ids, full_spec, db)

    # Step 8) Return the application requirements
    return full_spec


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


async def populate_database_specs():
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
    from codex.api_model import Indentifiers

    requirmenets = [
        ("Availability Checker", 1),
        ("Invoice Generator", 1),
        ("Appointment Optimization Tool", 1),
        ("Distance Calculator", 1),
        ("Profile Management System", 1),
    ]
    ids = Indentifiers(user_id=1, app_id=1)

    for task, app_id in requirmenets:
        spec = hardcoded_requirements(task)
        ids.app_id = app_id
        await create_spec(ids, spec)


if __name__ == "__main__":
    ids = Indentifiers(user_id=1, app_id=1)
    db_client = prisma.Prisma(auto_register=True)

    oai = openai.OpenAI()

    task = """The Tutor App is an app designed for tutors to manage their clients, schedules, and invoices.

It must support both the client and tutor scheduling, rescheduling and canceling appointments, and sending invoices after the appointment has passed.

Clients can sign up with OAuth2 or with traditional sign-in authentication. If they sign up with traditional authentication, it must be safe and secure. There will need to be password reset and login capabilities.

There will need to be authorization for identifying clients vs the tutor.

Additionally, it will have proper management of financials, including invoice management and payment tracking. This includes things like paid/failed invoice notifications, unpaid invoice follow-up, summarizing d/w/m/y income, and generating reports."""

    async def run_gen():
        await db_client.connect()
        output = await generate_requirements(
            ids=ids, app_name="Tutor", description=task
        )
        return output

    run(run_gen())
