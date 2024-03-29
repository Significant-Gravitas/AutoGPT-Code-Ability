import json
import logging
import traceback
from typing import Callable

from prisma import Json
from prisma.enums import DevelopmentPhase, Status
from prisma.models import EventLog

from codex.api_model import Identifiers


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
        await log_event(id, step, event, key, Status.FAILED, e)
        raise e


async def log_event(
    id: Identifiers,
    step: DevelopmentPhase,
    event: str,
    key: str,
    status: Status,
    data: Exception | object | None = None,
):
    if isinstance(data, Exception):
        data = traceback.format_exception(data)

    try:
        if data:
            data_str = Json(json.dumps(data))
        else:
            data_str = Json(None)
    except TypeError as e:
        # data is not serializable, store the error instead.
        data_str = Json(str(e))

    await EventLog.prisma().create(
        data={
            "userId": id.user_id,
            "applicationId": id.app_id,
            "event": event,
            "keyType": step,
            "keyValue": key,
            "status": status,
            "message": data_str,
        }
    )
