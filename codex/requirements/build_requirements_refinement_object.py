import enum
from typing import List
from pydantic import BaseModel
from pydantic import BaseModel
import enum
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


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
    def _missing_(cls, value: str):
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


def convert_requirements(requirements_qa) -> RequirementsRefined:
    requirements_refined = RequirementsRefined()

    for req_qa in requirements_qa:
        req_qa.question = req_qa.question.lower()
        match = process.extractOne(
            req_qa.question,
            [
                "do we need db?",
                "do we need an api for talking to a front end?",
                "do we need an api for talking to other services?",
                "do we need an api for other services talking to us?",
                "do we need to issue api keys for other services to talk to us?",
                "do we need monitoring?",
                "do we need internationalization?",
                "do we need analytics?",
                "is there monetization?",
                "is the monetization via a paywall or ads?",
                "does this require a subscription or a one-time purchase?",
                "is the whole service monetized or only part?",
                "is monetization implemented through authorization?",
                "do we need authentication?",
                "do we need authorization?",
                "what authorization roles do we need?",
            ],
            scorer=fuzz.ratio,
        )

        if match:
            matched_question = match[0]
            if fuzz.ratio(matched_question, req_qa.question) >= 80:
                if matched_question == "do we need db?":
                    requirements_refined.need_db = ReplyEnum(req_qa.answer)
                    requirements_refined.need_db_justification = req_qa.think
                elif (
                    matched_question == "do we need an api for talking to a front end?"
                ):
                    requirements_refined.need_frontend_api = ReplyEnum(req_qa.answer)
                    requirements_refined.need_frontend_api_justification = req_qa.think
                elif (
                    matched_question
                    == "do we need an api for talking to other services?"
                ):
                    requirements_refined.need_other_services_api = ReplyEnum(
                        req_qa.answer
                    )
                    requirements_refined.need_other_services_api_justification = (
                        req_qa.think
                    )
                elif (
                    matched_question
                    == "do we need an api for other services talking to us?"
                ):
                    requirements_refined.need_external_api = ReplyEnum(req_qa.answer)
                    requirements_refined.need_external_api_justification = req_qa.think
                elif (
                    matched_question
                    == "do we need to issue api keys for other services to talk to us?"
                ):
                    requirements_refined.need_api_keys = ReplyEnum(req_qa.answer)
                    requirements_refined.need_api_keys_justification = req_qa.think
                elif matched_question == "do we need monitoring?":
                    requirements_refined.need_monitoring = ReplyEnum(req_qa.answer)
                    requirements_refined.need_monitoring_justification = req_qa.think
                elif matched_question == "do we need internationalization?":
                    requirements_refined.need_internationalization = ReplyEnum(
                        req_qa.answer
                    )
                    requirements_refined.need_internationalization_justification = (
                        req_qa.think
                    )
                elif matched_question == "do we need analytics?":
                    requirements_refined.need_analytics = ReplyEnum(req_qa.answer)
                    requirements_refined.need_analytics_justification = req_qa.think
                elif matched_question == "is there monetization?":
                    requirements_refined.need_monetization = ReplyEnum(req_qa.answer)
                    requirements_refined.need_monetization_justification = req_qa.think
                elif matched_question == "is the monetization via a paywall or ads?":
                    requirements_refined.monetization_model = req_qa.answer
                    requirements_refined.monetization_model_justification = req_qa.think
                elif (
                    matched_question
                    == "does this require a subscription or a one-time purchase?"
                ):
                    requirements_refined.monetization_type = req_qa.answer
                    requirements_refined.monetization_type_justification = req_qa.think
                elif matched_question == "is the whole service monetized or only part?":
                    requirements_refined.monetization_scope = req_qa.answer
                    requirements_refined.monetization_scope_justification = req_qa.think
                elif (
                    matched_question
                    == "is monetization implemented through authorization?"
                ):
                    requirements_refined.monetization_authorization = ReplyEnum(
                        req_qa.answer
                    )
                    requirements_refined.monetization_authorization_justification = (
                        req_qa.think
                    )
                elif matched_question == "do we need authentication?":
                    requirements_refined.need_authentication = ReplyEnum(req_qa.answer)
                    requirements_refined.need_authentication_justification = (
                        req_qa.think
                    )
                elif matched_question == "do we need authorization?":
                    requirements_refined.need_authorization = ReplyEnum(req_qa.answer)
                    requirements_refined.need_authorization_justification = req_qa.think
                elif matched_question == "what authorization roles do we need?":
                    requirements_refined.authorization_roles = [
                        role.strip("[]") for role in req_qa.answer.split(",")
                    ]
                    requirements_refined.authorization_roles_justification = (
                        req_qa.think
                    )

    return requirements_refined
