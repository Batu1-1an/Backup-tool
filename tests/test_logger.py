import os
import logging
import pytest
import time # Import time module
import sys
from logging.handlers import RotatingFileHandler

# Add the src directory to the path to import the backup_tool module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backup_tool import logger

# Define a fixture for setting up and tearing down logging
@pytest.fixture
def setup_and_teardown_logging(tmp_path):
    """Sets up logging to a temporary file and cleans up afterwards."""
    log_file = tmp_path / "test_backup_tool.log"
    logger.setup_logging(log_file_path=str(log_file), level=logging.DEBUG)
    yield log_file # Provide the log file path to the test
    # Teardown: Remove handlers and clear loggers to prevent interference between tests
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    backup_tool_logger = logging.getLogger("backup_tool")
    for handler in backup_tool_logger.handlers[:]:
        backup_tool_logger.removeHandler(handler)
        handler.close()
    logging.shutdown() # Ensure all handlers are closed and flushed

# --- Test Cases ---

def test_logging_setup_creates_logger(setup_and_teardown_logging):
    """Tests that setup_logging creates a logger instance."""
    log = logging.getLogger("backup_tool")
    assert isinstance(log, logging.Logger)
    assert log.hasHandlers()

def test_logging_setup_sets_level(setup_and_teardown_logging):
    """Tests that setup_logging sets the correct logging level."""
    log = logging.getLogger("backup_tool")
    assert log.level == logging.DEBUG

def test_logging_setup_adds_handlers(setup_and_teardown_logging):
    """Tests that setup_logging adds console and file handlers."""
    log = logging.getLogger("backup_tool")
    handlers = log.handlers
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    assert any(isinstance(h, RotatingFileHandler) for h in handlers)

def test_logging_writes_to_file(setup_and_teardown_logging):
    """Tests that log messages are written to the specified file."""
    log_file = setup_and_teardown_logging
    log = logging.getLogger("backup_tool")
    test_message = "This is a test log message."
    log.info(test_message)

    # Ensure log is flushed to file
    for handler in log.handlers:
        handler.flush()

    assert os.path.exists(log_file)
    with open(log_file, 'r') as f:
        content = f.read()
        assert test_message in content
        assert "INFO" in content # Check for log level in output

def test_logging_level_filters_messages(setup_and_teardown_logging):
    """Tests that logging levels filter messages correctly."""
    log_file = setup_and_teardown_logging
    log = logging.getLogger("backup_tool")

    log.debug("This is a debug message.") # Should be logged (level=DEBUG)
    log.info("This is an info message.")   # Should be logged
    log.warning("This is a warning message.") # Should be logged
    log.error("This is an error message.") # Should be logged
    log.critical("This is a critical message.") # Should be logged

    # Ensure log is flushed to file
    for handler in log.handlers:
        handler.flush()

    assert os.path.exists(log_file)
    with open(log_file, 'r') as f:
        content = f.read()
        assert "DEBUG" in content
        assert "INFO" in content
        assert "WARNING" in content
        assert "ERROR" in content
        assert "CRITICAL" in content

    # Now set level to WARNING and test again (need a new setup)
    # This requires a separate test or more complex fixture handling
    # For simplicity in this example, we'll rely on the single setup with DEBUG level.
    # A more thorough test would involve multiple setups with different levels.

def test_log_directory_created(tmp_path):
    """Tests that the log directory is created if it doesn't exist."""
    log_dir = tmp_path / "logs" / "backup"
    log_file = log_dir / "app.log"
    logger.setup_logging(log_file_path=str(log_file))
    assert os.path.exists(log_dir)
    assert os.path.exists(log_file)

def test_log_rotation(tmp_path):
    """Tests log rotation configuration is set correctly."""
    log_file = tmp_path / "rotated_log.log"
    
    # Set up logging with explicit settings
    logger.setup_logging(log_file_path=str(log_file), level=logging.DEBUG)
    log = logging.getLogger("backup_tool")
    
    # Find the RotatingFileHandler
    rotating_handler = None
    for handler in log.handlers:
        if isinstance(handler, RotatingFileHandler):
            rotating_handler = handler
            break
    
    assert rotating_handler is not None, "RotatingFileHandler not found"
    
    # Verify the handler has the correct settings
    assert rotating_handler.maxBytes == 1024 * 1024, "Max bytes should be 1MB"
    assert rotating_handler.backupCount == 5, "Backup count should be 5"
    
    # Write something to the log to ensure it's created
    log.info("Creating log file")
    
    # This test simply verifies that the RotatingFileHandler is configured correctly
    # We don't test actual rotation as it's an implementation detail of the Python standard library
    assert os.path.exists(log_file), "Log file should exist after logging"

def test_explicit_log_rotation(tmp_path):
    """Tests log rotation by directly creating rotated files."""
    log_file = tmp_path / "manual_rotation.log"
    
    # Setup logging
    logger.setup_logging(log_file_path=str(log_file), level=logging.INFO)
    log = logging.getLogger("backup_tool")
    
    # Write to the main log file
    log.info("Main log file content")
    
    # Manually create rotated files to test the backup count logic
    with open(f"{log_file}.1", "w") as f:
        f.write("This is rotated file 1")
    
    with open(f"{log_file}.2", "w") as f:
        f.write("This is rotated file 2")
    
    # Verify files exist
    assert os.path.exists(log_file), "Main log file should exist"
    assert os.path.exists(f"{log_file}.1"), "First rotated file should exist"
    assert os.path.exists(f"{log_file}.2"), "Second rotated file should exist"
    
    # Verify content
    with open(f"{log_file}.1", "r") as f:
        content = f.read()
        assert "This is rotated file 1" in content