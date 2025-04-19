import os
import logging
import shutil
import errno

from . import config
from . import network

logger = logging.getLogger("backup_tool")

class RestoreError(Exception):
    """Custom exception for restore-related errors."""
    pass

def perform_restore(config_data, backup_timestamp, destination_path, conflict_strategy="overwrite"):
    """
    Performs the restore operation from a specific backup timestamp.

    Args:
        config_data (dict): The loaded configuration dictionary.
        backup_timestamp (str): The timestamp of the backup to restore from (e.g., "YYYYMMDD_HHMMSS").
        destination_path (str): The local path to restore the files to.
        conflict_strategy (str): Strategy for handling existing destination ('overwrite' or 'error').

    Raises:
        config.ConfigError: If the configuration data is invalid.
        network.NetworkError: If connecting to the network share fails.
        FileNotFoundError: If the specified backup timestamp directory is not found on the share.
        RestoreError: For errors during the restore process.
        Exception: For other unexpected errors during restore.
    """
    logger.info(f"Starting restore operation from backup timestamp: {backup_timestamp} to {destination_path}")

    connected_share_path = None
    share_path = None
    share_type = None
    try:
        backup_target = config_data.get("backup_target")

        if not backup_target or not isinstance(backup_target, dict):
             raise config.ConfigError("Invalid or missing 'backup_target' in configuration.")
        if "path" not in backup_target or "type" not in backup_target:
             raise config.ConfigError("Missing 'path' or 'type' in 'backup_target' configuration.")

        share_path = backup_target["path"]
        share_type = backup_target["type"]
        credentials = backup_target.get("credentials") # Optional

        # Connect to the network share
        connected_share_path = network.connect_to_share(share_path, share_type, credentials)
        logger.info(f"Successfully connected to share. Accessible path: {connected_share_path}")

        # Construct the path to the specific backup timestamp on the share
        hostname = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
        backup_source_base = os.path.join(connected_share_path, "backups", hostname, backup_timestamp)

        logger.info(f"Verifying backup source path exists on share: {backup_source_base}")
        if not os.path.exists(backup_source_base):
            raise FileNotFoundError(f"Backup timestamp directory not found on share: {backup_source_base}")
        if not os.path.isdir(backup_source_base):
             raise FileNotFoundError(f"Backup source path is not a directory: {backup_source_base}")


        # Ensure the local destination directory exists and handle conflicts
        if os.path.exists(destination_path):
            logger.info(f"Local destination directory already exists: {destination_path}")
            if conflict_strategy.lower() == 'error':
                raise RestoreError(f"Destination path already exists: {destination_path}. Conflict strategy is 'error'.")
            elif conflict_strategy.lower() == 'overwrite':
                 logger.warning(f"Destination path exists: {destination_path}. Conflict strategy is 'overwrite'. Files will be overwritten.")
                 # shutil.copytree with dirs_exist_ok=True handles the overwrite
            else:
                 logger.warning(f"Unknown conflict strategy: {conflict_strategy}. Defaulting to 'overwrite'.")
                 # shutil.copytree with dirs_exist_ok=True handles the overwrite
        else:
            logger.info(f"Creating local destination directory: {destination_path}")
            try:
                os.makedirs(destination_path)
            except OSError as e:
                if e.errno == errno.EACCES:
                    raise RestoreError(f"Permission denied to create destination directory: {destination_path}") from e
                else:
                    raise RestoreError(f"Error creating destination directory: {destination_path} - {e}") from e


        logger.info(f"Restoring from '{backup_source_base}' to '{destination_path}'...")

        try:
            # Use shutil.copytree with dirs_exist_ok=True to handle merging/overwriting
            shutil.copytree(backup_source_base, destination_path, dirs_exist_ok=True)
            logger.info("Restore operation finished.")
        except Exception as e:
            logger.error(f"Error during file copying for restore: {e}")
            raise RestoreError(f"Error during file copying for restore: {e}") from e


    except config.ConfigError as e:
        logger.error(f"Configuration error during restore: {e}")
        raise
    except network.NetworkError as e:
        logger.error(f"Network error during restore: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"Backup source not found during restore: {e}")
        raise
    except RestoreError as e:
        logger.error(f"Restore process error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during restore: {e}")
        raise
    finally:
        # Ensure disconnection from the network share
        if connected_share_path:
            try:
                disconnect_share_type = config_data.get("backup_target", {}).get("type") # Use config for disconnection type
                if disconnect_share_type:
                    # On Linux, we need the mount point to unmount, which is connected_share_path
                    # On Windows, disconnect_from_share uses the original share_path
                    path_to_disconnect = connected_share_path if network.is_linux() else share_path
                    network.disconnect_from_share(path_to_disconnect, disconnect_share_type)
                    logger.info("Successfully disconnected from share.")
                else:
                    logger.warning("Could not determine share type for disconnection.")
            except network.NetworkError as e:
                logger.error(f"Error during network disconnection: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during disconnection: {e}")


# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Assuming logging is already set up
    # from logger import setup_logging; setup_logging()

    dummy_config = {
        "backup_sources": ["/fake/source1"],
        "backup_target": {
            "path": "//fake_server/fake_share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    dummy_timestamp = "20231027_100000"
    dummy_destination = "./restored_files"

    print(f"Attempting to run perform_restore with dummy config and timestamp {dummy_timestamp} to {dummy_destination} (will likely fail due to fake share)...")
    try:
        perform_restore(dummy_config, dummy_timestamp, dummy_destination)
    except (config.ConfigError, network.NetworkError, FileNotFoundError, RestoreError, NotImplementedError) as e:
        print(f"Caught expected error during example restore attempt: {e}")
    except Exception as e:
        print(f"Caught unexpected error during example restore attempt: {e}")

    # Example with conflict strategy 'error' (will likely fail if dummy_destination exists)
    print(f"\nAttempting to run perform_restore with conflict_strategy='error' to {dummy_destination}...")
    try:
        # Create the dummy destination directory to simulate conflict
        os.makedirs(dummy_destination, exist_ok=True)
        perform_restore(dummy_config, dummy_timestamp, dummy_destination, conflict_strategy="error")
    except (config.ConfigError, network.NetworkError, FileNotFoundError, RestoreError, NotImplementedError) as e:
        print(f"Caught expected error during example restore attempt with conflict_strategy='error': {e}")
    except Exception as e:
        print(f"Caught unexpected error during example restore attempt with conflict_strategy='error': {e}")
    finally:
         # Clean up dummy destination if created
         if os.path.exists(dummy_destination):
             print(f"Cleaning up dummy destination: {dummy_destination}")
             shutil.rmtree(dummy_destination) # Clean up the directory