import prisma

import codex.api_model
import codex.requirements.model


async def generate_requirements(
    ids: codex.api_model.Identifiers,
) -> codex.requirements.model.Specification:
    app = await prisma.models.Application.prisma().find_first_or_raise(
        where={"id": ids.app_id}
    )
    pass
