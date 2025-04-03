import os
import logging
from datetime import datetime

DATATIME = datetime.now().strftime("%Y-%m-%d-%H%M%S")
LOG_FILE = f"saves/log/soap-{DATATIME}.log"

def setup_logger(
    name:str,
    level = logging.DEBUG,
    console:bool = False
):
    """
    Setup logger with the given module's name.
    """
    os.makedirs("saves/log", exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # file handler for logging to a file
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(level)

    # Formatter for the log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add a console handler if needed
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logger('soap')