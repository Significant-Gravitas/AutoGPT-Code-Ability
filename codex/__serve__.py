from dotenv import load_dotenv

load_dotenv()

from codex import __main__
from codex.common.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    __main__.serve()
