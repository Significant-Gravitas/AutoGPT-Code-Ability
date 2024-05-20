import logging
import traceback
from typing import Callable

from fastapi.responses import JSONResponse
from prisma.enums import DevelopmentPhase, Status
from prisma.errors import RecordNotFoundError
from prisma.models import EventLog

from codex.api_model import Identifiers

logger = logging.getLogger(__name__)


# This is a custom logger that prints the exception stack trace on error by default
class Logger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def error(self, msg, *args, **kwargs):
        if not kwargs.get("exc_info"):
            kwargs["exc_info"] = True
        super().error(msg, *args, **kwargs)


async def execute_and_log(
    id: Identifiers,
    step: DevelopmentPhase,
    event: str,
    key: str,
    func: Callable,
    *args,
    **kwargs,
):
    try:
        await log_event(id, step, event, key, Status.STARTED)
        result = await func(*args, **kwargs)
        await log_event(id, step, event, key, Status.SUCCESS)
        return result
    except Exception as e:
        error = "\n".join(traceback.format_exception(e)).split(
            "Traceback (most recent call last):"
        )[-1]
        logger.error(f"Error during {step} {event}: {error}")
        await log_event(id, step, event, key, Status.FAILED, error)

        status_code = (
            404
            if isinstance(e, RecordNotFoundError) or isinstance(e, FileNotFoundError)
            else 500
        )

        return JSONResponse(
            content={"error": str(e)},
            status_code=status_code,
        )


async def log_event(
    id: Identifiers,
    step: DevelopmentPhase,
    event: str,
    key: str,
    status: Status = Status.FAILED,
    data: str | None = None,
):
    if not EventLog.prisma()._client.is_connected():
        await EventLog.prisma()._client.connect()
    await EventLog.prisma().create(
        data={
            "userId": id.user_id,
            "applicationId": id.app_id,
            "event": event,
            "keyType": step,
            "keyValue": key,
            "status": status,
            "message": data,
        }
    )
