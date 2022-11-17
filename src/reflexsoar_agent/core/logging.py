import sys
from typing import Dict, List, Optional, Union

from loguru import logger

HANDLERS: Dict[str, Union[int, None]] = {
    'json': None,
    'stdout': None,
    'file': None
}


def formatter(message):

    print(message["process"].id)
    message = {
        "record_id": message["line"],
        "timestamp": message["time"].isoformat(),
        "level": message["level"].name,
        "message": message["message"],
        "module": message["module"],
        "name": message["name"],
        "pid": message["process"].id,
        "process_name": message["process"].name
    }

    return "{message}"
    # return json.dumps(message)


def setup_logging(log_path="reflexsoar_agent.log",
                  rotation=1,
                  retention=10,
                  handlers: Optional[List[str]] = None, level="INFO", init=False):
    """Sets up the logging for the agent and all of its components and modules

    Args:
        log_path (str, optional): The path to the log file. Defaults to "reflexsoar_agent.log".
        rotation (int, optional): The number of MBs to rotate the log file. Defaults to 1.
        retention (int, optional): The number of days to retain the log file. Defaults to 10.
        handlers (list, optional): The handlers to use. Defaults to ['stdout', 'file'].
        level (str, optional): The logging level. Defaults to "INFO".
        init (bool, optional): Whether or not to initialize the logger. Defaults to False.
    """

    if handlers is None:
        handlers = ['stdout', 'file']

    # Remove all existing handlers
    if init:
        logger.info("Initializing logger")
        logger.remove()

    # Establishes a logger for stdout and writing to a file
    for handler in handlers:
        if handler == 'file':
            HANDLERS['file'] = logger.add(log_path,
                                          rotation=f"{rotation} MB",
                                          retention=retention,
                                          compression="zip",
                                          enqueue=True,
                                          encoding='utf-8'
                                          )
        if handler == 'stdout':
            HANDLERS['stdout'] = logger.add(sys.stdout, enqueue=True)
        if handler == 'json':
            HANDLERS['json'] = logger.add(sys.stdout, format=formatter, enqueue=True)
