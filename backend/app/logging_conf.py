import logging
from structlog import wrap_logger


def get_logger(name: str = "smartlinkupdater"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)
    return wrap_logger(logger)
