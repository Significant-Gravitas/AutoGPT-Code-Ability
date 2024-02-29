from prisma.models import Interview, Question

from codex.api_model import Identifiers
from codex.interview.model import (
    InterviewDBBase,
    InterviewMessageOptionalId,
    InterviewMessageWithResponse,
)


async def create_interview(ids: Identifiers, interview: InterviewDBBase) -> Interview:
    new_interview = await Interview.prisma().create(
        data={
            "applicationId": ids.app_id,
            "userId": ids.user_id,
            "task": interview.project_description,
            "name": interview.app_name,
            "finished": interview.finished,
            "Questions": {
                "create": [
                    {
                        "question": q.content,
                        "tool": q.tool,
                    }
                    for q in interview.questions
                ]
            },
        },
        include={"Questions": True},
    )
    return new_interview


async def answer_questions(
    interview_id: str, answers: list[InterviewMessageWithResponse]
) -> Interview:
    for a in answers:
        # TODO: Check this exists in a better way
        await Question.prisma().find_unique_or_raise(
            where={"id": a.id, "interviewId": interview_id}
        )
        await Question.prisma().update(
            where={"id": a.id},
            data={
                "answer": a.response,
            },
        )
    interview = await Interview.prisma().find_unique_or_raise(
        where={"id": interview_id}, include={"Questions": True}
    )
    return interview


async def add_questions(
    interview_id: str, questions: list[InterviewMessageOptionalId]
) -> Interview:
    interview = await Interview.prisma().find_unique_or_raise(
        where={"id": interview_id}, include={"Questions": True}
    )
    # add questions
    for q in questions:
        question = await Question.prisma().create(
            data={
                "interviewId": interview_id,
                "question": q.content,
                "tool": q.tool,
            }
        )
        # logger.debug(f"Added question {question.id} to interview {interview_id}")

    new_interview = await Interview.prisma().find_unique_or_raise(
        where={"id": interview_id}, include={"Questions": True}
    )
    return new_interview


async def finsh_interview(
    interview_id: str, finished_content: str, finished_text: str
) -> Interview:
    interview = await Interview.prisma().find_unique_or_raise(
        where={"id": interview_id}, include={"Questions": True}
    )
    updated_interview = await Interview.prisma().update(
        where={"id": interview_id},
        data={
            "finished": True,
            "Questions": {
                "create": [
                    {
                        "question": finished_content,
                        "answer": finished_text,
                        "tool": "finished",
                    }
                ]
            },
        },
    )
    return updated_interview


# async def update_interview(interview_id: str, interview: InterviewDBBase) -> Interview:
#     updated_interview = await Interview.prisma().update(
#         where={"id": interview_id},
#         data={
#             "description": interview.project_description,
#             "name": interview.app_name,
#         },
#     )
#     return updated_interview


async def get_interview(user_id: str, app_id: str, interview_id: str) -> Interview:
    interview = await Interview.prisma().find_first_or_raise(
        where={
            "id": interview_id,
            "userId": user_id,
            "applicationId": app_id,
        },
        include={"Questions": True},
    )

    return interview


async def delete_interview(interview_id: str) -> None:
    await Interview.prisma().update(
        where={"id": interview_id},
        data={"deleted": True},
    )


# async def list_interviews(
#     user_id: str, app_id: str, page: int, page_size: int
# ) -> InterviewsListResponse:
#     skip = (page - 1) * page_size
#     total_items = await Interview.prisma().count(
#         where={"userId": user_id, "applicationId": app_id, "deleted": False}
#     )
#     if total_items > 0:
#         interviews = await Interview.prisma().find_many(
#             where={"userId": user_id, "applicationId": app_id, "deleted": False},
#             include={},
#             skip=skip,
#             take=page_size,
#         )

#         total_pages = (total_items + page_size - 1) // page_size

#         # interviews_response = [
#         #     SpecificationResponse.from_specification(spec) for spec in specs
#         # ]

#         pagination = Pagination(
#             total_items=total_items,
#             total_pages=total_pages,
#             current_page=page,
#             page_size=page_size,
#         )

#         return InterviewsListResponse(specs=interviews_response, pagination=pagination)
#     else:
#         return InterviewsListResponse(
#             specs=[],
#             pagination=Pagination(
#                 total_items=0, total_pages=0, current_page=0, page_size=0
#             ),
#         )
