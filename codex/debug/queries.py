import math
import os

from prisma import Prisma
from sqlalchemy import create_engine, text

import codex.api_model
import codex.common.model


async def fetch_application_details(
    page=1, page_size=20
) -> codex.common.model.ResumePointsList:
    client = Prisma()

    await client.connect()

    async_engine = create_engine(
        os.environ["DATABASE_URL"].replace("postgres", "postgresql"), echo=True
    )
    # Pagination parameters
    offset = (page - 1) * page_size

    # Connect to the database using the async engine
    with async_engine.connect() as conn:
        # Pagination parameters
        offset = (page - 1) * page_size

        # Raw SQL query
        raw_sql = text(
            """
            SELECT
                a."userId" AS user_id,
                a.name AS name,
                a."updatedAt" AS "updatedAt",
                a.id AS application_id,
                i.id AS interview_id,
                s.id AS spec_id,
                ca.id AS completed_app_id,
                d.id AS deployment_id
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
            ORDER BY
                a."updatedAt" DESC
            LIMIT :limit OFFSET :offset
        """
        )

        count_raw_sql = text(
            """
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
        )

        # Execute the query
        results = conn.execute(
            raw_sql, {"limit": page_size, "offset": offset}
        ).fetchall()
        count = conn.execute(count_raw_sql).fetchone()
        if count:
            count = count[0]
        else:
            count = 0
        print(f"Raw Quest Results: {results}")

        # Process the results
        resume_points = [
            codex.common.model.ResumePoint(
                userId=result[0],
                name=result[1],
                updatedAt=result[2],
                applicationId=result[3],
                interviewId=result[4],
                specificationId=result[5],
                completedAppId=result[6],
                deploymentId=result[7],
            )
            for result in results
        ]

    pages = codex.api_model.Pagination(
        total_items=count,
        total_pages=math.ceil(count / page_size),
        current_page=page,
        page_size=page_size,
    )

    await client.disconnect()

    return codex.common.model.ResumePointsList(
        resume_points=resume_points, pagination=pages
    )
