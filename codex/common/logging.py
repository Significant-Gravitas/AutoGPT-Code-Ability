import logging


# This is a custom logger that prints the exception stack trace on error by default
class Logger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def error(self, msg, *args, **kwargs):
        if not kwargs.get("exc_info"):
            kwargs["exc_info"] = True
        super().error(msg, *args, **kwargs)


# def getLogger(name):
#     return setup_logging(Logger(name))
