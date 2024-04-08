import logging.config
import os

import coloredlogs


def setup_logging():
    local_mode = os.environ.get("RUN_ENV", "CLOUD").lower() == "local"
    file_path = os.path.abspath(__file__)
    cloud_config = os.path.join(os.path.dirname(file_path), "log_config_cloud.ini")
    if local_mode:
        log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        # Set up basic configuration with standard output
        logging.basicConfig(level=logging.INFO, format=log_format)
        coloredlogs.install(level="INFO", fmt=log_format)

        # Create a file handler for error messages
        file_handler = logging.FileHandler("codex_logs.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))

        # Create a file handler for error messages
        err_file_handler = logging.FileHandler("error_logs.log")
        err_file_handler.setLevel(logging.ERROR)
        err_file_handler.setFormatter(logging.Formatter(log_format))

        # Add the file handler to the root logger
        logging.getLogger().addHandler(file_handler)
        logging.getLogger().addHandler(err_file_handler)
    else:
        logging.config.fileConfig(cloud_config)

    # Set the log level for the httpx library to warning
    logging.getLogger("httpx").setLevel(logging.WARNING)
