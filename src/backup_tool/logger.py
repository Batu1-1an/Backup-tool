import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file_path="backup_tool.log", level=logging.INFO):
    """
    Sets up the logging configuration for the backup tool.

    Args:
        log_file_path (str): The path to the log file.
        level (int): The minimum logging level (e.g., logging.INFO, logging.DEBUG).
    """
    # Ensure the log directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a logger
    logger = logging.getLogger("backup_tool")
    logger.setLevel(level)

    # Create handlers
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # File handler with rotation (max 1MB per file, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=1024 * 1024, # 1MB
        backupCount=5
    )
    file_handler.setLevel(level)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatters to handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    # Prevent adding handlers multiple times if setup_logging is called more than once
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    # Example usage:
    # logger = logging.getLogger("backup_tool")
    # logger.info("Logging setup complete.")
    # logger.error("An example error.")

if __name__ == "__main__":
    # Example of setting up and using logging
    setup_logging("test_backup_tool.log", logging.DEBUG)
    logger = logging.getLogger("backup_tool")
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    print("\nCheck test_backup_tool.log for file output.")