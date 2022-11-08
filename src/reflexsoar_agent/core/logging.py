import sys
from loguru import logger


def setup_logging():
    logger.remove()
    logger.add("reflexsoar_agent.log", rotation="1 MB", compression="zip", enqueue=True, encoding='utf-8')
    logger.add(sys.stdout, enqueue=True)
