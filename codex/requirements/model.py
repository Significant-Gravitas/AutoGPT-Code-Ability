import enum
import logging
from dataclasses import dataclass
from typing import Callable, List, Literal, Optional, Type

from prisma.enums import AccessLevel
from pydantic import BaseModel, ConfigDict

from codex.common.ai_block import AIBlock

logger = logging.getLogger(__name__)

Q_AND_A_FORMAT = """- "{question}": "{answer}"
"""

Q_AND_A_FORMAT_WITH_THOUGHTS = """- "{question}": "{answer}" : Reasoning: "{thoughts}"
"""


class DecomposeTask(BaseModel):
    # Placeholder until so I have something to test the ai_block with
    thoughts: str
    project_description: str
    requirements: List[str]
    api_routes: List[str]


# Data Model
@dataclass
class QandA:
    question: str
    thoughts: str
    project_manager: str
    software_architect: str
    subject_matter_expert: str
    team_answer: str
    was_conclusive: str


class WrappedQA(BaseModel):
    wrapper: QandA


class QandAResponses(BaseModel):
    think: str
    answer: list[WrappedQA]
    closing_thoughts: Optional[str]


@dataclass
class Clarification(BaseModel):
    question: str
    answer: str
    thoughts: str


@dataclass
class SimpleResult(BaseModel):
    think: str
    answer: str


@dataclass
class Requirements(BaseModel):
    thoughts: str
    name: str
    description: str

    def __str__(self):
        return f"#### {self.name}\n##### Thoughts\n{self.thoughts}\n##### Description\n{self.description}"


# class RequirementWrapper(BaseModel):
#     requirement: Requirements

#     def __str__(self) -> str:
#         return self.requirement.__str__()


@dataclass(repr=True)
class ReqObj:
    functional: list[Requirements]
    nonfunctional: list[Requirements]

    def __str__(self) -> str:
        functionals = ""
        for item in self.functional:
            functionals += item.__str__() + "\n"
        nonfunctionals = ""
        for item in self.nonfunctional:
            nonfunctionals += item.__str__() + "\n"
        return f"### Functional Requirements\n{functionals}\n### Nonfunctional Requirements\n{nonfunctionals}"


class RequirementsGenResponse(BaseModel):
    think: str
    answer: ReqObj


@dataclass
class RequirementsQA:
    question: str
    think: str
    answer: str | list[str]


class Feature(BaseModel):
    name: str
    thoughts: str
    description: str
    considerations: str
    risks: str
    needed_external_tools: str
    priority: str

    def __str__(self) -> str:
        return f"#### {self.name}\n##### Description\n{self.description}\n##### Considerations\n{self.considerations}\n##### Risks\n{self.risks}\n##### External Tools Required\n{self.needed_external_tools}\n##### Priority: {self.priority}"


class FeatureWrapper(BaseModel):
    feature: Feature


class FeaturesSuperObject(BaseModel):
    think: str
    project_name: str
    description: str
    general_feature_thoughts: str
    features: list[FeatureWrapper]


# class WrappedRequirementsQA(BaseModel):
#     wrapper: RequirementsQA


class RequirementsResponse(BaseModel):
    think: str
    answer: list[RequirementsQA]


class ModuleRefinementRequirement(BaseModel):
    name: str
    description: str

    def __str__(self):
        return f"#### Requirement: {self.name}\n{self.description}\n"


class Parameter(BaseModel):
    name: str
    param_type: str
    description: str

    def __str__(self):
        return f"- **Name**: {self.name}\n  - **Type**: {self.param_type}\n  - **Description**: {self.description}\n"


class RequestModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

    def __str__(self):
        params_str = "\n".join(param.__str__() for param in self.params)
        return f"###### {self.name}\n**Description**: {self.description}\n\n**Parameters**:\n{params_str}\n"


class ResponseModel(BaseModel):
    name: str
    description: str
    params: List[Parameter]

    def __str__(self):
        params_str = "\n".join(param.__str__() for param in self.params)
        return f"###### {self.name}\n**Description**: {self.description}\n\n**Parameters**:\n{params_str}\n"


class DatabaseTable(BaseModel):
    name: str | None = None
    description: str
    definition: str  # prisma model for a table

    def __str__(self):
        return f"**{self.name}**\n\n**Description**: {self.description}\n\n**Definition**:\n```\n{self.definition}\n```\n"


class DatabaseSchema(BaseModel):
    name: str  # name of the database schema
    description: str  # context on what the database schema is
    tables: List[DatabaseTable]  # list of tables in the database schema

    def __str__(self):
        tables_str = "\n".join(str(table) for table in self.tables)
        return f"## {self.name}\n**Description**: {self.description}\n**Tables**:\n{tables_str}\n"


class EndpointDataModel(BaseModel):
    name: str
    description: Optional[str]
    params: List[Parameter]


class NewAPIModel(BaseModel):
    name: str
    description: Optional[str]
    params: List[Parameter]


class APIEndpointWrapper(BaseModel):
    request_model: NewAPIModel
    response_model: NewAPIModel


class EndpointSchemaRefinementResponse(BaseModel):
    think: str
    db_models_needed: list[str]
    new_api_models: list[NewAPIModel]
    api_endpoint: APIEndpointWrapper
    end_thoughts: Optional[str]


class Endpoint(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str
    type: Literal[
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        "CONNECT",
        "OPTIONS",
        "TRACE",
        "PATCH",
    ]
    description: str
    path: str
    request_model: Optional[RequestModel]
    response_model: Optional[ResponseModel]
    data_models: Optional[List[EndpointDataModel]]
    database_schema: Optional[DatabaseSchema]

    def __str__(self):
        request_response_text = ""
        data_model_text = ""
        database_text = ""
        if self.request_model:
            request_response_text += f"##### Request: `{self.request_model.__str__() or 'Not defined yet'}`\n"
        if self.response_model:
            request_response_text += f"##### Response:`{self.request_model.__str__() or 'Not defined yet'}`\n"
        if self.data_models:
            data_model_text += "\n\n".join(
                [data_model.__str__() for data_model in self.data_models]
            )
        if self.database_schema:
            database_text += (
                f"##### Database Schema\n\n{self.database_schema.__str__()}"
            )
        return f"##### {self.name}: `{self.type} {self.path}`\n\n{self.description}\n\n{request_response_text}\n\n{data_model_text}\n\n{database_text}"


class EndpointGroupWrapper(BaseModel):
    group_category: str
    endpoints: list[Endpoint]


class ModuleRefinementModule(BaseModel):
    module_name: str
    rough_requirements: str
    thoughts: str
    new_description: str
    module_requirements: list[ModuleRefinementRequirement]
    module_links: list[str]
    endpoint_groups_list: Optional[list[str]]
    endpoint_groups: list[EndpointGroupWrapper]


class ModuleRefinement(BaseModel):
    modules: list[ModuleRefinementModule]


class Module(BaseModel):
    name: str
    description: str
    requirements: Optional[List[ModuleRefinementRequirement]]
    endpoints: Optional[List[Endpoint]]
    related_modules: Optional[List[str]]

    def __str__(self):
        text = ""
        text += f"### Module: {self.name}\n#### Description\n{self.description}\n"
        if self.requirements:
            text += "#### Requirements\n"
            for requirement in self.requirements:
                text += requirement.__str__() + "\n"
        if self.endpoints:
            text += "#### Endpoints\n"
            for endpoint in self.endpoints:
                text += endpoint.__str__() + "\n"
        if self.related_modules:
            text += "#### Related Modules\n"
            for related_module in self.related_modules:
                text += related_module + "\n"
        return f"{text}"


class ModuleResponse(BaseModel):
    think_general: str
    think_anti: str
    modules: List[Module]

    def __str__(self) -> str:
        answer_str = "\n".join(str(x) for x in self.modules)
        return f"Thoughts: {self.think_general}\nAnti:{self.think_anti}\n{answer_str}"


# class DBSchemaTableResponseWrapper(BaseModel):
#     table: DatabaseTable


class DBSchemaResponseWrapper(BaseModel):
    # name of the database schema
    name: str
    # context on what the database schema is
    description: str
    # list of tables in the database schema
    tables: List[DatabaseTable]


class PreAnswer(BaseModel):
    tables: list[dict[str, str]]
    enums: list[dict[str, str]]


class DBResponse(BaseModel):
    think: str
    anti_think: str
    plan: str
    refine: str
    pre_answer: PreAnswer
    pre_answer_issues: str
    full_schema: str
    database_schema: DBSchemaResponseWrapper
    conclusions: str


class ReplyEnum(enum.Enum):
    YES = "yes"
    NO = "no"
    NA = "na"
    UNANSWERED = "unanswered"

    def __eq__(self, other):
        if self is ReplyEnum.NA:
            return False
        return super().__eq__(other)

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            value = value.replace("/", "").lower()
            if value.lower() == "yes":
                return ReplyEnum.YES
            elif value.lower() == "no":
                return ReplyEnum.NO
            elif value.lower() == "na":
                return ReplyEnum.NA
        raise ValueError(f"{value} is not a valid ReplyEnum")


class RequirementsRefined(BaseModel):
    need_db: ReplyEnum = ReplyEnum.UNANSWERED
    need_db_justification: str = ""

    need_frontend_api: ReplyEnum = ReplyEnum.UNANSWERED
    need_frontend_api_justification: str = ""

    need_other_services_api: ReplyEnum = ReplyEnum.UNANSWERED
    need_other_services_api_justification: str = ""

    need_external_api: ReplyEnum = ReplyEnum.UNANSWERED
    need_external_api_justification: str = ""

    need_api_keys: ReplyEnum = ReplyEnum.UNANSWERED
    need_api_keys_justification: str = ""

    need_monitoring: ReplyEnum = ReplyEnum.UNANSWERED
    need_monitoring_justification: str = ""

    need_internationalization: ReplyEnum = ReplyEnum.UNANSWERED
    need_internationalization_justification: str = ""

    need_analytics: ReplyEnum = ReplyEnum.UNANSWERED
    need_analytics_justification: str = ""

    need_monetization: ReplyEnum = ReplyEnum.UNANSWERED
    need_monetization_justification: str = ""

    monetization_model: str = "No Answer"
    monetization_model_justification: str = ""

    monetization_type: str = "No Answer"
    monetization_type_justification: str = ""

    monetization_scope: str = "No Answer"
    monetization_scope_justification: str = ""

    monetization_authorization: ReplyEnum = ReplyEnum.UNANSWERED
    monetization_authorization_justification: str = ""

    need_authentication: ReplyEnum = ReplyEnum.UNANSWERED
    need_authentication_justification: str = ""

    need_authorization: ReplyEnum = ReplyEnum.UNANSWERED
    need_authorization_justification: str = ""

    authorization_roles: List[str] = []
    authorization_roles_justification: str = ""

    dirty_requirements: Optional[list[RequirementsQA]]


class DatabaseSchemaRequirement(BaseModel):
    thoughts: str
    prisma_table_models: List[str]


class APIRouteRequirement(BaseModel):
    # I'll use these to generate the endpoint
    method: str
    path: str

    function_name: str

    # This is context on what this api route should do
    description: str

    # This is the access level required to access this api route
    access_level: AccessLevel

    # This is the model for the request and response
    request_model: RequestModel
    response_model: ResponseModel

    # This is the database schema this api route will use
    # I'm thinking it will be a prisma table schema or maybe a list of table schemas
    # See the schema.prisma file in the codex directory more info
    database_schema: DatabaseSchema | None = None
    data_models: Optional[List[EndpointDataModel]] = None

    def __str__(self):
        db_schema_str = (
            f"**Database Schema**:\n{str(self.database_schema)}\n"
            if self.database_schema
            else ""
        )
        return (
            f"**Method**: `{self.method}`\n"
            f"**Path**: `{self.path}`\n"
            f"**Function Name**: `{self.function_name}`\n"
            f"**Description**: {self.description}\n"
            f"**Request Model**:\n{str(self.request_model)}\n"
            f"**Response Model**:\n{str(self.response_model)}\n"
            f"{db_schema_str}"
        )


class ApplicationRequirements(BaseModel):
    # Application name
    name: str
    # Context on what the application is
    context: str

    api_routes: List[APIRouteRequirement] | None = None

    def __str__(self):
        if not self.api_routes:
            return f"# {self.name}\n**Context**: {self.context}\n"
        api_routes_str = "\n".join(str(route) for route in self.api_routes)
        return f"# {self.name}\n**Context**: {self.context}\n**API Routes**:\n{api_routes_str}\n"


# Running State Object Dict


class StateObj:
    def __init__(self, task: str):
        self.task = task
        self.project_description: str
        self.project_description_thoughts: str
        self.clarifying_questions: list[Clarification] = []
        self.q_and_a: list[QandA] = []
        self.product_description: str
        self.product_name: str
        self.features: list[Feature] = []
        self.requirements_q_and_a: list[RequirementsQA] = []
        self.refined_requirement_q_a: RequirementsRefined
        self.requirements: ReqObj
        self.modules: list[Module] = []
        self.database: Optional[DatabaseSchema] = None

    @staticmethod
    def convert_to_q_and_a_format(
        question: str, answer: str, thoughts: str | None = None
    ) -> str:
        if thoughts:
            return Q_AND_A_FORMAT_WITH_THOUGHTS.format(
                question=question, answer=answer, thoughts=thoughts
            )
        return Q_AND_A_FORMAT.format(question=question, answer=answer)

    def conclusive_q_and_a(self) -> list[QandA]:
        conclusive: list[QandA] = []
        for qa in self.q_and_a:
            if qa.was_conclusive and qa.was_conclusive == "Yes":
                conclusive.append(qa)
            else:
                logger.info(f"Maybe an oopsie here? {qa}")
        return conclusive

    def conclusive_q_and_a_as_string(self) -> str:
        conclusive = self.conclusive_q_and_a()
        output = ""
        for qa in conclusive:
            output += self.convert_to_q_and_a_format(
                qa.question, qa.team_answer, qa.thoughts
            )
        return output

    def add_clarifying_question(self, clarifying_question: Clarification) -> None:
        if not self.clarifying_questions:
            self.clarifying_questions = []
        self.clarifying_questions.append(clarifying_question)

    def clarifying_questions_as_string(self) -> str:
        output = ""
        for clarifcation in self.clarifying_questions:
            output += self.convert_to_q_and_a_format(
                question=clarifcation.question,
                answer=clarifcation.answer,
                thoughts=clarifcation.thoughts,
            )
        return output

    def joint_q_and_a(self) -> str:
        return (
            self.clarifying_questions_as_string() + self.conclusive_q_and_a_as_string()
        )

    def requirements_q_and_a_string(self) -> str:
        output: str = ""
        for req in self.requirements_q_and_a:
            answer_text = (
                req.answer if isinstance(req.answer, str) else "\n".join(req.answer)
            )
            output += self.convert_to_q_and_a_format(
                req.question, answer_text, req.think
            )
        return output

    def __repr__(self):
        # Provide default representations for potentially uninitialized attributes
        project_description = repr(getattr(self, "project_description", "None"))
        project_description_thoughts = repr(
            getattr(self, "project_description_thoughts", "None")
        )
        clarifying_questions = repr(getattr(self, "clarifying_questions", []))
        q_and_a = repr(getattr(self, "q_and_a", []))
        product_description = repr(getattr(self, "product_description", "None"))
        product_name = repr(getattr(self, "product_name", "None"))
        features = repr(getattr(self, "features", []))
        requirements_q_and_a = repr(getattr(self, "requirements_q_and_a", []))
        requirements = repr(getattr(self, "requirements", "None"))
        modules = repr(getattr(self, "modules", []))

        return (
            f"StateObj(task={self.task!r}, project_description={project_description}, "
            f"project_description_thoughts={project_description_thoughts}, "
            f"clarifying_questions={clarifying_questions}, q_and_a={q_and_a}, "
            f"product_description={product_description}, product_name={product_name}, "
            f"features={features}, requirements_q_and_a={requirements_q_and_a}, "
            f"requirements={requirements}, modules={modules})"
        )

    def __str__(self):
        # Provide default values or representations for potentially uninitialized attributes
        project_description = getattr(self, "project_description", "Not provided")
        product_description = getattr(self, "product_description", "Not provided")
        product_name = getattr(self, "product_name", "Not provided")
        features = getattr(self, "features", [])
        clarifying_questions = getattr(self, "clarifying_questions", [])
        requirements_q_and_a = getattr(self, "requirements_q_and_a", [])
        modules: List[Module] = getattr(self, "modules", [])

        modules_text = "\n".join(module.__str__() for module in modules if module)
        requirements_text = self.requirements.__str__()
        requirements_q_and_a_text = self.requirements_q_and_a_string()
        features_text = "\n".join(feature.__str__() for feature in self.features)
        clarifying_questions_text = self.clarifying_questions_as_string()
        conclusive_q_and_a_text = self.conclusive_q_and_a_as_string()
        if hasattr(self, "database") and self.database:
            database_text = self.database.__str__()
        else:
            database_text = "Database Not Yet Generated"
        return f"""# {product_name}\n
## Task \n{self.task}\n
### Project Description\n{project_description}\n
### Product Description\n{product_description}\n
### Features\n{features_text}\n
### Clarifiying Questions\n{clarifying_questions_text}\n
### Conclusive Q&A\n{conclusive_q_and_a_text}\n
### Requirement Q&A\n{requirements_q_and_a_text}\n
### Requirements\n{requirements_text}\n
### Modules\n{modules_text}
### Database Design\n{database_text}"""
