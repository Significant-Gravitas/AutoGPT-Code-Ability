import math

from prisma import Prisma
from pydantic import BaseModel

import codex.api_model
import codex.common.model


async def fetch_application_details(
    page=1, page_size=20
) -> codex.common.model.ResumePointsList:
    client = Prisma()

    await client.connect()

    # Pagination parameters
    offset = (page - 1) * page_size

    # Pagination parameters
    offset = (page - 1) * page_size

    # Raw SQL query
    raw_sql = """
        SELECT
            CAST(ROW_NUMBER() OVER (ORDER BY a."updatedAt" DESC) AS VARCHAR) AS id,
            a.name AS name,
            a."updatedAt" AS "updatedAt",
            a."userId" AS "userId",
            a.id AS "applicationId",
            i.id AS "interviewId",
            s.id AS "specificationId",
            ca.id AS "completedAppId",
            d.id AS "deploymentId"
        FROM
            "Application" a
        LEFT JOIN
            "Interview" i ON a.id = i."applicationId" AND i.deleted = false
        LEFT JOIN
            "Specification" s ON i.id = s."interviewId" AND s.deleted = false
        LEFT JOIN
            "CompletedApp" ca ON s.id = ca."specificationId" AND ca.deleted = false
        LEFT JOIN
            "Deployment" d ON ca.id = d."completedAppId" AND d.deleted = false
        WHERE
            a.deleted = false
        ORDER BY
            a."updatedAt" DESC
        LIMIT $1 OFFSET $2
    """

    count_raw_sql = """
        SELECT
            COUNT(*)
        FROM
            "Application" a
        LEFT JOIN
            "Interview" i ON a.id = i."applicationId" AND i.deleted = false
        LEFT JOIN
            "Specification" s ON a.id = s."applicationId" AND s.deleted = false
        LEFT JOIN
            "CompletedApp" ca ON s.id = ca."specificationId" AND ca.deleted = false
        LEFT JOIN
            "Deployment" d ON ca.id = d."completedAppId" AND d.deleted = false
        WHERE
            a.deleted = false
    """

    # Execute the query
    results = await client.query_raw(
        raw_sql,
        page_size,
        offset,
        model=codex.common.model.ResumePoint,
    )

    class CountResponse(BaseModel):
        count: int

    count_resp = await client.query_first(count_raw_sql, model=CountResponse)
    count = 0
    if count_resp:
        count = count_resp.count

    pages = codex.api_model.Pagination(
        total_items=count,
        total_pages=math.ceil(count / page_size),
        current_page=page,
        page_size=page_size,
    )

    await client.disconnect()

    return codex.common.model.ResumePointsList(resume_points=results, pagination=pages)
