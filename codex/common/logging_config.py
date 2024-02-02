import logging.config
import os


def setup_logging(local: bool = False):
    file_path = os.path.abspath(__file__)
    local_config = os.path.join(os.path.dirname(file_path), "log_config_local.ini")
    cloud_config = os.path.join(os.path.dirname(file_path), "log_config_cloud.ini")
    if local:
        logging.config.fileConfig(local_config)
    else:
        logging.config.fileConfig(cloud_config)
    
    # Set the log level for the httpx library to warning
    logging.getLogger('httpx').setLevel(logging.WARNING)
