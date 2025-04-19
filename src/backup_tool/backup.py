import os
import logging
import datetime
import shutil
import time
import errno
import re # Import regex module

from . import config
from . import network

logger = logging.getLogger("backup_tool")

class BackupError(Exception):
    """Custom exception for backup-related errors."""
    pass

def copy_with_progress(src, dst, buffer_size=4096, progress_interval=1):
    """
    Copies a file from src to dst with progress reporting.

    Args:
        src (str): Source file path.
        dst (str): Destination file path.
        buffer_size (int): Size of the buffer for copying in bytes.
        progress_interval (int): Interval in seconds for reporting progress.

    Raises:
        BackupError: If a file operation fails during copying.
    """
    try:
        file_size = os.stat(src).st_size
        copied_size = 0
        last_report_time = time.time()

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        logger.info(f"Copying file: {src} to {dst} ({file_size} bytes)")

        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                buf = fsrc.read(buffer_size)
                if not buf:
                    break
                fdst.write(buf)
                copied_size += len(buf)

                current_time = time.time()
                if current_time - last_report_time >= progress_interval:
                    progress_percent = (copied_size / file_size) * 100 if file_size > 0 else 100
                    logger.info(f"  Progress: {copied_size}/{file_size} bytes ({progress_percent:.2f}%)")
                    last_report_time = current_time

        # Final progress report to ensure 100% is shown
        progress_percent = (copied_size / file_size) * 100 if file_size > 0 else 100
        logger.info(f"  Progress: {copied_size}/{file_size} bytes ({progress_percent:.2f}%) - Complete")

    except FileNotFoundError:
        raise BackupError(f"Source file not found during copy: {src}")
    except PermissionError:
        raise BackupError(f"Permission denied during copy of {src} to {dst}")
    except IOError as e:
        raise BackupError(f"IO error during copy of {src} to {dst}: {e}")
    except Exception as e:
        raise BackupError(f"An unexpected error occurred during copy of {src} to {dst}: {e}")


def perform_rotation_and_pruning(config_data, connected_share_path):
    """
    Performs backup rotation and pruning based on the configuration.

    Args:
        config_data (dict): The loaded configuration dictionary.
        connected_share_path (str): The path to the connected network share.
    """
    logger.info("Performing backup rotation and pruning...")

    retention_policy = config_data.get("retention_policy")
    if not retention_policy or not isinstance(retention_policy, dict):
        logger.info("No retention policy configured. Skipping rotation and pruning.")
        return

    keep_last = retention_policy.get("keep_last")
    if keep_last is None or not isinstance(keep_last, int) or keep_last < 0:
        logger.warning("Invalid or missing 'keep_last' in retention policy. Skipping rotation and pruning.")
        return

    hostname = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
    backup_base_dir = os.path.join(connected_share_path, "backups", hostname)

    if not os.path.exists(backup_base_dir):
        logger.info(f"Backup base directory not found: {backup_base_dir}. No backups to prune.")
        return

    try:
        # List all items in the backup base directory
        all_items = os.listdir(backup_base_dir)

        # Filter for directories that look like backup timestamps (YYYYMMDD_HHMMSS)
        backup_dirs = []
        timestamp_pattern = re.compile(r"^\d{8}_\d{6}$")
        for item in all_items:
            item_path = os.path.join(backup_base_dir, item)
            if os.path.isdir(item_path) and timestamp_pattern.match(item):
                try:
                    # Attempt to parse the timestamp to ensure it's valid
                    datetime.datetime.strptime(item, "%Y%m%d_%H%M%S")
                    backup_dirs.append(item)
                except ValueError:
                    logger.warning(f"Directory '{item}' in backup base directory does not match timestamp format. Skipping.")
                    continue


        # Sort backup directories by timestamp (oldest first)
        backup_dirs.sort()

        # Determine which backups to remove
        backups_to_remove = backup_dirs[:-keep_last] if len(backup_dirs) > keep_last else []

        if not backups_to_remove:
            logger.info(f"No backups to prune. Keeping the last {len(backup_dirs)} backups.")
            return

        logger.info(f"Found {len(backup_dirs)} backups. Keeping the last {keep_last}. Removing {len(backups_to_remove)} backups.")

        # Remove old backups
        for old_backup_dir in backups_to_remove:
            old_backup_path = os.path.join(backup_base_dir, old_backup_dir)
            logger.info(f"Removing old backup: {old_backup_path}")
            try:
                shutil.rmtree(old_backup_path)
                logger.info(f"Successfully removed old backup: {old_backup_path}")
            except OSError as e:
                 logger.error(f"Error removing old backup directory {old_backup_path}: {e}")
            except Exception as e:
                 logger.error(f"An unexpected error occurred while removing old backup {old_backup_path}: {e}")

        logger.info("Backup rotation and pruning finished.")

    except Exception as e:
        logger.error(f"An unexpected error occurred during backup rotation and pruning: {e}")


def find_latest_backup(connected_share_path, hostname):
    """
    Finds the path to the latest backup for a given hostname on the share.

    Args:
        connected_share_path (str): The path to the connected network share.
        hostname (str): The hostname of the machine being backed up.

    Returns:
        str or None: The path to the latest backup directory, or None if no backups are found.
    """
    backup_base_dir = os.path.join(connected_share_path, "backups", hostname)

    if not os.path.exists(backup_base_dir):
        return None

    try:
        # List all items in the backup base directory
        all_items = os.listdir(backup_base_dir)

        # Filter for directories that look like backup timestamps (YYYYMMDD_HHMMSS)
        backup_dirs = []
        timestamp_pattern = re.compile(r"^\d{8}_\d{6}$")
        for item in all_items:
            item_path = os.path.join(backup_base_dir, item)
            if os.path.isdir(item_path) and timestamp_pattern.match(item):
                try:
                    # Attempt to parse the timestamp to ensure it's valid
                    datetime.datetime.strptime(item, "%Y%m%d_%H%M%S")
                    backup_dirs.append(item)
                except ValueError:
                    continue # Skip directories that don't match the timestamp format

        if not backup_dirs:
            return None

        # Sort backup directories by timestamp (latest last)
        backup_dirs.sort()

        # The last directory in the sorted list is the latest backup
        latest_backup_dir = backup_dirs[-1]
        return os.path.join(backup_base_dir, latest_backup_dir)

    except Exception as e:
        logger.error(f"An error occurred while finding the latest backup: {e}")
        return None


def perform_backup(config_data, source_override=None, target_override=None, incremental=False):
    """
    Performs the backup operation based on the provided configuration,
    with optional overrides for source and target.

    Args:
        config_data (dict): The loaded configuration dictionary.
        source_override (list, optional): A list of source paths to backup.
                                           If provided, overrides 'backup_sources' in config.
        target_override (dict, optional): A dictionary defining the backup target.
                                          If provided, overrides 'backup_target' in config.
        incremental (bool, optional): If True, perform an incremental backup. Defaults to False.

    Raises:
        config.ConfigError: If the configuration data or overrides are invalid.
        network.NetworkError: If connecting to the network share fails.
        BackupError: For errors during the backup process.
        Exception: For other unexpected errors.
    """
    logger.info(f"Starting {'incremental' if incremental else 'full'} backup operation...")

    connected_share_path = None
    try:
        # Use overrides if provided, otherwise use config data
        backup_sources = source_override if source_override is not None else config_data.get("backup_sources")
        backup_target = target_override if target_override is not None else config_data.get("backup_target")

        if not backup_sources or not isinstance(backup_sources, list):
            raise config.ConfigError("Invalid or missing 'backup_sources' in configuration or override.")
        if not backup_target or not isinstance(backup_target, dict):
             raise config.ConfigError("Invalid or missing 'backup_target' in configuration or override.")
        if "path" not in backup_target or "type" not in backup_target:
             raise config.ConfigError("Missing 'path' or 'type' in 'backup_target' configuration or override.")

        share_path = backup_target["path"]
        share_type = backup_target["type"]
        credentials = backup_target.get("credentials") # Optional

        # Connect to the network share
        connected_share_path = network.connect_to_share(share_path, share_type, credentials)
        logger.info(f"Successfully connected to share. Accessible path: {connected_share_path}")

        # Create a timestamped directory for the current backup on the share
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
        backup_destination_base = os.path.join(connected_share_path, "backups", hostname, timestamp)

        logger.info(f"Creating backup destination directory: {backup_destination_base}")
        try:
            os.makedirs(backup_destination_base, exist_ok=True) # Create directories on the share
        except OSError as e:
            # Catch specific OS errors during directory creation
            if e.errno == errno.EACCES:
                raise BackupError(f"Permission denied to create backup directory on share: {backup_destination_base}") from e
            else:
                raise BackupError(f"Error creating backup directory on share: {backup_destination_base} - {e}") from e


        latest_backup_path = None
        if incremental:
            latest_backup_path = find_latest_backup(connected_share_path, hostname)
            if latest_backup_path:
                logger.info(f"Found latest backup for incremental comparison: {latest_backup_path}")
            else:
                logger.info("No previous backup found for incremental backup. Performing a full backup instead.")
                incremental = False # Fallback to full backup if no previous found


        # Iterate through backup sources and copy them
        for source_path in backup_sources:
            if not os.path.exists(source_path):
                logger.warning(f"Backup source not found, skipping: {source_path}")
                continue

            # Determine the correct destination path on the share for this source
            if os.path.isabs(source_path):
                 if network.is_windows():
                      path_parts = os.path.splitdrive(source_path)
                      relative_source_path = path_parts[1].lstrip(os.sep)
                 else: # Linux/Unix-like
                      relative_source_path = source_path.lstrip(os.sep)
            else:
                 relative_source_path = source_path


            destination_path = os.path.join(backup_destination_base, relative_source_path)

            logger.info(f"Processing backup source: '{source_path}'")

            try:
                if os.path.isdir(source_path):
                    logger.info(f"Copying directory tree: {source_path} to {destination_path}")
                    # Ensure parent directory exists on the share before copying
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                    if incremental and latest_backup_path:
                        # TODO: Implement incremental directory copy logic
                        # Compare source_path with its counterpart in latest_backup_path
                        # Copy only new/modified files and directories
                        logger.warning("Incremental directory backup not yet fully implemented. Performing full copy for now.")
                        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
                    else:
                        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)

                    logger.info(f"Successfully copied directory tree: {source_path}")
                else:
                    # Handle files
                    if incremental and latest_backup_path:
                        # TODO: Implement incremental file copy logic
                        # Compare source_path with its counterpart in latest_backup_path
                        # Copy only if file is new or modified (check size and modification time)
                        latest_source_path_in_backup = os.path.join(latest_backup_path, relative_source_path)
                        if os.path.exists(latest_source_path_in_backup):
                            # Compare file stats (size and mtime)
                            source_stat = os.stat(source_path)
                            backup_stat = os.stat(latest_source_path_in_backup)

                            if source_stat.st_size == backup_stat.st_size and int(source_stat.st_mtime) == int(backup_stat.st_mtime):
                                logger.info(f"File '{source_path}' unchanged. Skipping incremental copy.")
                                continue # Skip copying if file is unchanged
                            else:
                                logger.info(f"File '{source_path}' changed. Copying incrementally.")
                                copy_with_progress(source_path, destination_path) # Copy the changed file
                        else:
                            logger.info(f"File '{source_path}' is new. Copying incrementally.")
                            copy_with_progress(source_path, destination_path) # Copy new file
                    else:
                        # Use the custom copy_with_progress for full backup of files
                        copy_with_progress(source_path, destination_path)

                    logger.info(f"Successfully copied file: {source_path}")

                logger.info(f"Successfully processed backup source: {source_path}")

            except (FileNotFoundError, PermissionError, IOError, BackupError, Exception) as e:
                # Catch specific errors during file/directory operations
                error_message = f"Error backing up '{source_path}': {e}"
                logger.error(error_message)
                # Log the error and continue with the next source
                # If a critical error occurs (e.g., network disconnect), it will be caught by the outer except block


        logger.info(f"{'Incremental' if incremental else 'Full'} backup operation finished.")

        # Perform backup rotation and pruning after a successful backup
        perform_rotation_and_pruning(config_data, connected_share_path)


    except config.ConfigError as e:
        logger.error(f"Configuration error during backup: {e}")
        raise # Re-raise the exception to be handled by the caller (e.g., main.py)
    except network.NetworkError as e:
        logger.error(f"Network error during backup: {e}")
        raise # Re-raise the exception
    except BackupError as e:
        logger.error(f"Backup process error: {e}")
        raise # Re-raise the exception
    except Exception as e:
        logger.error(f"An unexpected error occurred during backup: {e}")
        raise # Re-raise the exception
    finally:
        # Ensure disconnection from the network share
        if connected_share_path:
            try:
                # Need the original share_type for disconnection
                # Use target_override if available, otherwise fall back to config
                disconnect_share_type = target_override.get("type") if target_override is not None else config_data.get("backup_target", {}).get("type")
                if disconnect_share_type:
                    network.disconnect_from_share(connected_share_path, disconnect_share_type)
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
    # For standalone testing, you might need to set up logging and create a dummy config
    # from logger import setup_logging; setup_logging()

    dummy_config = {
        "backup_sources": ["/fake/source1", "/fake/source2"],
        "backup_target": {
            "path": "//fake_server/fake_share",
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }

    print("Attempting to run perform_backup with dummy config (will likely fail due to fake share)...")
    try:
        perform_backup(dummy_config)
    except (config.ConfigError, network.NetworkError, BackupError, NotImplementedError) as e:
        print(f"Caught expected error during example backup attempt: {e}")
    except Exception as e:
        print(f"Caught unexpected error during example backup attempt: {e}")

    print("\nAttempting to run perform_backup with source override...")
    try:
        perform_backup(dummy_config, source_override=["/fake/override_source"])
    except (config.ConfigError, network.NetworkError, BackupError, NotImplementedError) as e:
        print(f"Caught expected error during example backup attempt with source override: {e}")
    except Exception as e:
        print(f"Caught unexpected error during example backup attempt with source override: {e}")

    print("\nAttempting to run perform_backup with target override...")
    try:
        override_target = {
             "path": "//fake_override_server/fake_override_share",
             "type": "nfs"
        }
        perform_backup(dummy_config, target_override=override_target)
    except (config.ConfigError, network.NetworkError, BackupError, NotImplementedError) as e:
        print(f"Caught expected error during example backup attempt with target override: {e}")
    except Exception as e:
        print(f"Caught unexpected error during example backup attempt with target override: {e}")

    print("\nAttempting to run incremental backup with dummy config...")
    try:
        perform_backup(dummy_config, incremental=True)
    except (config.ConfigError, network.NetworkError, BackupError, NotImplementedError) as e:
        print(f"Caught expected error during example incremental backup attempt: {e}")
    except Exception as e:
        print(f"Caught unexpected error during example incremental backup attempt: {e}")