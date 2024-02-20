import logging


# This is a custom logger that prints the exception stack trace on error by default
class Logger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)

    def error(self, msg, *args, **kwargs):
        super().error(msg, *args, **kwargs, exc_info=True)


def getLogger(name):
    return Logger(name)
