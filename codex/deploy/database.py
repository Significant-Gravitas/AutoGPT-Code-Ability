from prisma.models import Deployment

from codex.api_model import DeploymentMetadata, DeploymentsListResponse, Pagination


async def get_deployment(deployment_id: int) -> Deployment:
    deployment = await Deployment.prisma().find_unique_or_raise(
        where={"id": deployment_id},
    )

    return deployment


async def delete_deployment(deployment_id: int) -> None:
    await Deployment.prisma().update(
        where={
            "id": deployment_id,
        },
        data={"deleted": True},
    )


async def list_deployments(
    user_id: int, deliverable_id: int, page: int, page_size: int
) -> DeploymentsListResponse:
    skip = (page - 1) * page_size

    total_items = await Deployment.count(
        where={
            "deliverable_id": deliverable_id,
            "userId": user_id,
        }
    )
    if total_items == 0:
        return DeploymentsListResponse(
            deployments=[],
            pagination=Pagination(
                total_items=0, total_pages=0, current_page=0, page_size=0
            ),
        )

    deployments = await Deployment.find_many(
        skip=skip,
        take=page_size,
        where={
            "deliverable_id": deliverable_id,
            "userId": user_id,
        },
    )

    ret_deployments = [
        DeploymentMetadata(
            id=deployment.id,
            createdAt=deployment.createdAt,
            fileName=deployment.fileName,
            fileSize=deployment.fileSize,
        )
        for deployment in deployments
    ]

    total_pages = (total_items + page_size - 1) // page_size

    pagination = Pagination(
        total_items=total_items,
        total_pages=total_pages,
        current_page=page,
        page_size=page_size,
    )

    return DeploymentsListResponse(deployments=ret_deployments, pagination=pagination)
