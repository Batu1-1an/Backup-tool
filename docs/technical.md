# Technical Documentation

This document provides technical details for the Python Backup & Restoration Tool.

## Technologies

### Core Technologies
- **Python 3.7+**: Primary programming language
- **PyYAML 6.0+**: YAML configuration file parsing
- **schedule 1.2+**: Job scheduling library for automated backups

### Network Technologies
- **SMB Protocol**: Server Message Block protocol support for Windows-style network shares
- **NFS Protocol**: Network File System protocol support for Unix-style network shares
- **os.path**: Cross-platform path handling (Note: `pathlib` could be considered for future refactoring)

### Operating Systems
- **Windows 10+**: Full support for Windows environments
- **Linux (Major Distributions)**: Full support for Linux environments
  - Ubuntu 18.04+
  - CentOS/RHEL 7+
  - Debian 10+

## Implementation Details

### Configuration System
The configuration system uses YAML for human-readable configuration. The `config.py` module handles:
- Loading the YAML file via PyYAML
- Validating the structure and required fields (including sources, target, logging, schedule, retention_policy)
- Providing a normalized configuration object to other modules
- Supporting environment variable expansion for sensitive values

Example configuration validation:
```python
def validate_config(config):
    """Validate the loaded configuration."""
    required_fields = ['backup_sources', 'backup_target'] # Logging and schedule are optional
    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Missing required configuration field: {field}")

    # Validate backup target
    if 'path' not in config['backup_target']:
        raise ConfigError("Backup target must specify a path")
    if 'type' not in config['backup_target']:
        raise ConfigError("Backup target must specify a type (smb or nfs)")

    # Validate retention policy (if present)
    if 'retention_policy' in config and isinstance(config['retention_policy'], dict):
        if 'keep_last' not in config['retention_policy'] or not isinstance(config['retention_policy']['keep_last'], int):
             logger.warning("Invalid 'keep_last' in retention policy. Must be an integer.")
```

### Network Share Connectivity
The `network.py` module implements OS-specific functions to connect/disconnect from network shares:

```python
# Example (Conceptual - actual implementation is OS-specific)
def connect_to_share(share_path, share_type, credentials=None):
    """Connects to the specified network share."""
    if is_windows():
        # Windows connection logic (e.g., net use)
        pass
    elif is_linux():
        # Linux connection logic (e.g., mount)
        pass
    else:
        raise NetworkError("Unsupported operating system")
    # Return the accessible path (e.g., mount point or UNC path)
    return accessible_path
```

### Backup Process
The backup process is implemented in `backup.py` and follows these steps:
1. Connect to the network share (`network.py`).
2. (Incremental Only) Find the latest backup timestamp (`backup.py`).
3. Create a new timestamped directory structure on the target (`backup.py`).
4. Iterate through all source paths (`backup.py`).
5. For each source:
    - Determine the relative path.
    - (Incremental Only) Compare with the corresponding path in the latest backup.
    - Copy files/directories only if new or modified (using size/mtime comparison for files). Use `copy_with_progress` for file transfers.
6. Log success/failure for each file/directory (`logger.py`).
7. Perform backup rotation and pruning based on `retention_policy` in config (`backup.py`).
8. Disconnect from the network share (`network.py`).

### Restore Process
The restore process is implemented in `restore.py` and follows these steps:
1. Connect to the network share (`network.py`).
2. Verify the specified backup timestamp directory exists on the share.
3. Ensure the local destination path exists or create it.
4. Handle conflicts if the destination exists based on the `conflict_strategy` (`overwrite` or `error`).
5. Copy files/directories from the selected backup timestamp directory to the destination using `shutil.copytree`.
6. Log restore operations (`logger.py`).
7. Disconnect from the network share (`network.py`).

### Scheduler Implementation
The scheduler (`scheduler.py`) uses the `schedule` library to manage backup timing:
- Loads configuration to find `schedule` settings (daily, weekly).
- Sets up jobs using `schedule.every().<unit>.at().do()`.
- Calls `backup.perform_backup` for scheduled jobs.
- Includes a placeholder (`send_error_notification`) for notifying on job failures.
- Runs in an infinite loop checking for pending jobs.

```python
def configure_schedule(config_data):
    """Set up the backup schedule based on configuration."""
    schedule_config = config_data.get("schedule", {})
    if 'daily' in schedule_config:
        schedule.every().day.at(schedule_config['daily']).do(run_backup_job, config_data=config_data)

    if 'weekly' in schedule_config:
        # ... parsing and scheduling logic ...
        getattr(schedule.every(), day_of_week).at(weekly_time).do(run_backup_job, config_data=config_data)
```

### Cross-Platform Considerations
- Path handling uses `os.path` for OS-agnostic operations.
- OS-specific operations (like network share mounting/mapping) are isolated in `network.py` using conditional checks (`is_windows()`, `is_linux()`).
- Hostname retrieval uses `os.uname()` where available.

## APIs

### Command Line Interface (`main.py`)

The tool provides the following CLI commands:

```
backup_tool backup [OPTIONS]
backup_tool restore [OPTIONS]
backup_tool schedule [OPTIONS]
```

#### backup
```
Usage: backup_tool backup [OPTIONS]

Options:
  --config PATH          Path to configuration file [default: config/backup_config.yaml]
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                         Set the logging level [default: INFO]
  --log-file PATH        Path to the log file (overrides config)
  --source PATH...       Specific source(s) to backup (overrides config)
  # --incremental        # TODO: Add CLI flag for incremental backup
  --help                 Show this message and exit
```

#### restore
```
Usage: backup_tool restore [OPTIONS]

Options:
  --config PATH          Path to configuration file [default: config/backup_config.yaml]
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                         Set the logging level [default: INFO]
  --log-file PATH        Path to the log file (overrides config)
  --backup-timestamp TEXT  Timestamp of the backup to restore from (YYYYMMDD_HHMMSS) [required]
  --destination PATH     Destination path to restore to [required]
  --conflict-strategy [overwrite|error]
                         Strategy for handling existing destination [default: overwrite]
  --help                 Show this message and exit
```

#### schedule
```
Usage: backup_tool schedule [OPTIONS]

Options:
  --config PATH          Path to configuration file [default: config/backup_config.yaml]
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                         Set the logging level [default: INFO]
  --log-file PATH        Path to the log file (overrides config)
  # --foreground         # TODO: Add flag to run scheduler in foreground
  --help                 Show this message and exit
```

### Module APIs

#### config.py
```python
load_config(config_path: str) -> dict
# Validation happens internally during load
```

#### backup.py
```python
perform_backup(config_data: dict, source_override: list = None, target_override: dict = None, incremental: bool = False) -> None
perform_rotation_and_pruning(config_data: dict, connected_share_path: str) -> None
find_latest_backup(connected_share_path: str, hostname: str) -> str | None
copy_with_progress(src: str, dst: str, buffer_size: int = 4096, progress_interval: int = 1) -> None
```

#### restore.py
```python
perform_restore(config_data: dict, backup_timestamp: str, destination_path: str, conflict_strategy: str = "overwrite") -> None
```

#### network.py
```python
connect_to_share(share_path: str, share_type: str, credentials: dict = None) -> str # Returns accessible path
disconnect_from_share(path_to_disconnect: str, share_type: str) -> None
is_windows() -> bool
is_linux() -> bool
```

#### logger.py
```python
setup_logging(log_file_path: str = "backup_tool.log", level: int = logging.INFO) -> None
```

#### scheduler.py
```python
run_scheduled_backups(config_path: str) -> None
run_backup_job(config_data: dict) -> None
send_error_notification(error_message: str) -> None # Placeholder