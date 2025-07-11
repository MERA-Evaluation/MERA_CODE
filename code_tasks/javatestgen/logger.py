import os
import logging
from datetime import datetime

LOG_LEVEL_CONSOLE = logging.DEBUG
LOG_LEVEL_FILE    = logging.DEBUG

def setup_logger(LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")):
    os.makedirs(LOG_DIR, exist_ok=True)  # Create the logs directory if it doesn't exist
    # This is (faster then setup pyproject to work with empty folder)

    # Log file name with today's date
    log_filename = datetime.now().strftime("%Y-%m-%d.log")
    log_filepath = os.path.join(LOG_DIR, log_filename)

    # Logging format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Get the root logger
    logger = logging.getLogger("java_testgen_bench")

    if not logger.hasHandlers():  # Ensure we don't add duplicate handlers
        # Set up the root logger
        logger.setLevel(logging.DEBUG)  # Set the highest level for the root logger

        # Formatter
        formatter = logging.Formatter(LOG_FORMAT)

        # Console handler (LOG_LEVEL_CONSOLE)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL_CONSOLE)  # Set log level for console
        console_handler.setFormatter(formatter)

        # File handler (LOG_LEVEL_FILE)
        file_handler = logging.FileHandler(log_filepath, mode="a")
        file_handler.setLevel(LOG_LEVEL_FILE)  # Set log level for file
        file_handler.setFormatter(formatter)

        # Add handlers to the root logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logger.info("Logger initialized and logs will be saved to %s", log_filepath)
    