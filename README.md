# Python Backup & Restoration Tool

## Overview

This project is a Python-based command-line tool designed to automate the backup of specified files and directories from Linux and Windows servers to a network share (SMB/NFS). It also provides functionality for manually restoring files from these backups, with features like backup rotation and initial support for incremental backups.

## Features

*   **Configurable:** Uses a YAML configuration file to define backup sources, target, schedule, and **retention policies for backup rotation**.
*   **Cross-Platform:** Supports running on both Linux and Windows operating systems.
*   **Network Share Support:** Designed to back up to and restore from SMB or NFS network shares.
*   **Scheduled Backups:** Allows scheduling daily and weekly automated backups.
*   **Manual Operations:** Provides command-line options for triggering manual backups and restores, **including specifying sources and handling restore conflicts**.
*   **Logging:** Logs all operations for monitoring and troubleshooting, **with configurable log rotation**.
*   **Backup Rotation & Pruning:** Implements policies to automatically remove older backups based on configuration.
*   **Incremental Backup (In Progress):** Includes initial support for performing incremental backups by comparing against the latest existing backup.
*   **Enhanced Error Handling:** Improved error handling and recovery mechanisms for network issues and file operations.

## Project Structure

```
backup_tool/
├── src/
│   ├── backup_tool/
│   │   ├── __init__.py       # Package initialization
│   │   ├── config.py       # Configuration loading and validation
│   │   ├── backup.py       # Core backup logic (includes rotation/pruning, incremental logic)
│   │   ├── restore.py      # Core restore logic (includes conflict handling)
│   │   ├── scheduler.py    # Scheduling logic (includes error notification placeholder)
│   │   ├── network.py      # Network share connection logic (SMB/NFS)
│   │   └── logger.py       # Logging setup
│   └── main.py             # Entry point for the CLI
├── tests/                  # Unit and integration tests
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_network.py
│   ├── test_backup.py
│   ├── test_restore.py
│   └── test_placeholder.py
├── docs/                   # Documentation
│   ├── architecture.md     # System architecture
│   ├── backup_tool_plan.md # Project plan
│   ├── directory_structure.md # Project directory structure
│   ├── error_documentation.md # Documented errors and solutions
│   ├── lessons_learned.md  # Project insights and lessons
│   ├── memory.md           # Overall project context and status
│   ├── product_requirement_docs.md # Product requirements
│   ├── technical.md        # Technical details and APIs
│   └── usage.md            # Usage instructions (TODO: Needs expansion)
├── config/                 # Example configuration files
│   └── backup_config.yaml.example
├── requirements.txt        # Project dependencies
└── README.md               # Project overview and setup instructions (This file)
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Batu1-1an/Backup-tool.-
    cd Backup-tool.- # Note: Directory name matches repo name
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    # On Linux/macOS
    python3 -m venv .venv
    source .venv/bin/activate

    # On Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the tool:**
    *   Copy the example configuration file:
        ```bash
        # On Linux/macOS
        cp config/backup_config.yaml.example config/backup_config.yaml
        # On Windows
        copy config\backup_config.yaml.example config\backup_config.yaml
        ```
    *   Edit `config/backup_config.yaml` to specify your backup sources, target network share details, schedule, and retention policy. **Be cautious with credentials and consider using secure methods like environment variables.**

## Usage

The tool provides the following command-line interface:

```
backup_tool [COMMAND] [OPTIONS]
```

### Commands:

*   `backup`: Trigger a manual backup.
*   `restore`: Restore files from a backup.
*   `schedule`: Start the scheduler for automated backups.

### `backup` Command

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
*   Use `--source` followed by one or more paths to back up specific files or directories instead of those defined in the config.

### `restore` Command

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
*   `--backup-timestamp` is required and specifies which backup set to restore from (e.g., `20231027_103000`).
*   `--destination` is required and specifies the local path where files will be restored.
*   `--conflict-strategy` determines how to handle files that already exist at the destination.

### `schedule` Command

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
*   This command starts the background scheduler process that will run backups according to the `schedule` defined in your configuration file.

## Development

*   **Running Tests:** Navigate to the `backup_tool` directory and run `pytest`.
    ```bash
    cd backup_tool
    pytest
    ```
*   **Contributing:** (TODO: Add contribution guidelines)

## License

(TODO: Add license information)