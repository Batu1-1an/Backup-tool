<div align="center">
  <h1>Backup Tool</h1>
  <p><strong>Cross-platform CLI tool for automated file backup and restoration to SMB/NFS network shares</strong></p>

  <a href="#"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python 3.7+"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey.svg" alt="Platform: Windows | Linux"></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <a href="#"><img src="https://img.shields.io/badge/tests-passing-brightgreen.svg" alt="Tests: Passing"></a>
</div>

---

## Overview

Backup Tool is a Python-based command-line utility designed to automate the backup of critical files and directories from Linux and Windows servers to network shares via **SMB** or **NFS** protocols. It supports scheduled automated backups, manual on-demand backups, file restoration with conflict handling, backup rotation and pruning, and incremental backup capabilities.

---

## Features

- **YAML Configuration** — Human-readable config for sources, targets, schedules, and retention policies
- **SMB / NFS Support** — Native SMB (CIFS) and NFS network share connectivity on both Windows and Linux
- **Scheduled Backups** — Daily and weekly automated scheduling via the `schedule` library
- **Manual Backup & Restore** — CLI commands for on-demand backups and point-in-time restores
- **Backup Rotation & Pruning** — Retention policy with configurable `keep_last` to automatically prune old backups
- **Incremental Backups** — Initial support for file-level incremental backup (size/mtime comparison)
- **Progress Reporting** — Real-time progress tracking during file copy operations
- **Configurable Logging** — Rotating file logging with configurable levels and log file paths
- **Environment Variable Expansion** — Securely reference credentials and paths via `${VAR}` in config
- **Source & Target Overrides** — Override backup sources or targets at runtime via CLI arguments
- **Cross-Platform** — Runs on Windows 10+ and major Linux distributions
- **Comprehensive Error Handling** — Granular error handling with graceful continuation on per-file failures

---

## Tech Stack

| Component             | Technology                                                                 |
|-----------------------|----------------------------------------------------------------------------|
| Language              | [Python 3.7+](https://www.python.org/)                                     |
| Config Parsing        | [PyYAML 6.0+](https://pyyaml.org/)                                         |
| Job Scheduling        | [schedule 1.2+](https://github.com/dbader/schedule)                        |
| Network Protocols     | SMB (CIFS) · NFS                                                           |
| Testing               | [pytest 8.1+](https://docs.pytest.org/) · `unittest.mock`                  |
| CLI Framework         | Python `argparse` (standard library)                                       |

---

## Prerequisites

- **Python 3.7 or higher**
- Network access to an SMB or NFS share
- Appropriate read permissions for source files/directories
- Appropriate write permissions on the backup target share
- **Linux only:** `sudo` access for mounting CIFS/NFS shares; `cifs-utils` package recommended

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Batu1-1an/Backup-tool.git
   cd Backup-tool
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Install in development mode:**

   ```bash
   pip install -e .
   ```

---

## Configuration

Copy the example configuration and edit it to match your environment:

```bash
# Linux / macOS
cp config/backup_config.yaml.example config/backup_config.yaml

# Windows
copy config\backup_config.yaml.example config\backup_config.yaml
```

### Full Configuration Reference

```yaml
# --- Backup Sources ---
# List of files and directories to back up (absolute paths).
backup_sources:
  - /var/log/syslog
  - /etc/nginx/nginx.conf
  - /home/user/documents

# --- Backup Target ---
# Network share where backups will be stored.
backup_target:
  path: //your_backup_server/backup_share   # SMB: //server/share | NFS: server:/export
  type: smb                                  # "smb" or "nfs"
  credentials:                               # Optional; use env vars for security
    username: ${BACKUP_USER}
    password: ${BACKUP_PASS}

# --- Schedule ---
# Automated backup schedule (daily and/or weekly).
schedule:
  daily: "02:00"              # HH:MM (24-hour)
  weekly: "Sunday 03:00"      # Day HH:MM

# --- Retention Policy ---
# Automatically prune old backups, keeping only the N most recent.
retention_policy:
  keep_last: 30               # Number of most recent backups to retain

# --- Logging ---
logging:
  log_file: /var/log/backup_tool/backup_tool.log   # or C:\Logs\backup_tool.log
  level: INFO                                       # DEBUG | INFO | WARNING | ERROR | CRITICAL
```

> **Security:** Use environment variables (`${VAR}` syntax) for credentials. The config loader automatically expands them at runtime.

---

## Usage

### Command Structure

```bash
backup_tool [--config PATH] [--log-level LEVEL] [--log-file PATH] <command> [OPTIONS]
```

### Available Commands

| Command     | Description                                       |
|-------------|---------------------------------------------------|
| `backup`    | Run a manual backup                               |
| `restore`   | Restore files from a specific backup timestamp     |
| `schedule`  | Start the scheduler for automated backups          |

### `backup` — Manual Backup

```bash
backup_tool backup [OPTIONS]

Options:
  --config PATH         Config file path (default: config/backup_config.yaml)
  --source PATH...      Override source paths (space-separated)
  --log-level LEVEL     Logging level (default: INFO)
  --log-file PATH       Log file path (overrides config)
  --help                Show help message
```

**Examples:**

```bash
# Backup with default configuration
backup_tool backup

# Backup specific sources only
backup_tool backup --source /etc/nginx /home/user/documents

# Backup with custom config and debug logging
backup_tool backup --config /etc/backup_tool/prod.yaml --log-level DEBUG
```

### `restore` — Restore from Backup

```bash
backup_tool restore --backup-timestamp <YYYYMMDD_HHMMSS> --destination <PATH> [OPTIONS]

Options:
  --config PATH               Config file path
  --backup-timestamp TEXT      Backup timestamp to restore from [required]
  --destination PATH           Local destination path [required]
  --conflict-strategy STRATEGY  "overwrite" or "error" (default: overwrite)
  --log-level LEVEL            Logging level
  --log-file PATH              Log file path
  --help                       Show help message
```

**Examples:**

```bash
# Restore to a specific location, overwriting existing files
backup_tool restore --backup-timestamp 20231027_103000 --destination /tmp/restore

# Restore with error-on-conflict strategy (safety first)
backup_tool restore --backup-timestamp 20231027_103000 --destination /tmp/restore --conflict-strategy error
```

### `schedule` — Automated Scheduler

```bash
backup_tool schedule [OPTIONS]

Options:
  --config PATH     Config file path
  --log-level LEVEL  Logging level
  --log-file PATH    Log file path
  --help             Show help message
```

Runs indefinitely, executing backups according to the schedule defined in the configuration file.

---

## Project Structure

```
Backup-tool/
├── config/
│   └── backup_config.yaml.example   # Example configuration template
├── docs/                             # Project documentation
│   ├── architecture.md
│   ├── backup_tool_plan.md
│   ├── directory_structure.md
│   ├── error_documentation.md
│   ├── lessons_learned.md
│   ├── memory.md
│   ├── product_requirement_docs.md
│   ├── technical.md
│   └── usage.md
├── src/
│   ├── backup_tool/                  # Core package
│   │   ├── __init__.py               # Package init
│   │   ├── config.py                 # YAML config loader & validator
│   │   ├── backup.py                 # Backup engine (full + incremental)
│   │   ├── restore.py                # Restore engine with conflict handling
│   │   ├── scheduler.py              # Automated job scheduler
│   │   ├── network.py                # SMB/NFS share connectivity
│   │   └── logger.py                 # Rotating file + console logging
│   └── main.py                       # CLI entry point
├── tasks/                            # Project management & task tracking
│   ├── active_context.md
│   └── tasks_plan.md
├── tests/                            # Unit and integration tests
│   ├── test_config.py
│   ├── test_backup.py
│   ├── test_restore.py
│   ├── test_network.py
│   ├── test_logger.py
│   └── test_placeholder.py
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## Testing

The project uses **pytest** with `unittest.mock` for comprehensive unit testing.

```bash
# Run all tests
pytest -v

# Run tests for a specific module
pytest tests/test_config.py -v
pytest tests/test_backup.py -v
pytest tests/test_network.py -v

# Run with coverage (if pytest-cov is installed)
pytest --cov=backup_tool tests/
```

---

## Module API Reference

| Module      | Key Functions                                                                                 |
|-------------|------------------------------------------------------------------------------------------------|
| `config`    | `load_config(path)` — Load and validate YAML config                                            |
| `backup`    | `perform_backup(config, source_override, target_override, incremental)` — Execute backup       |
| `restore`   | `perform_restore(config, timestamp, destination, conflict_strategy)` — Execute restore         |
| `network`   | `connect_to_share(path, type, creds)` / `disconnect_from_share(path, type)` — Manage shares    |
| `scheduler` | `run_scheduled_backups(config_path)` — Start the automated scheduler                           |
| `logger`    | `setup_logging(file_path, level)` — Configure rotating file + console logging                  |

---

## Roadmap

- [x] YAML configuration with validation & env var expansion
- [x] SMB / NFS network share connectivity (Windows + Linux)
- [x] Full backup with progress reporting
- [x] File restore with conflict handling (`overwrite` / `error`)
- [x] Daily & weekly job scheduling
- [x] Backup rotation and pruning (retention policy)
- [x] Incremental backup (file-level size/mtime comparison)
- [ ] Compression options for backup archives
- [ ] Encryption for sensitive backup data
- [ ] Email / webhook error notifications
- [ ] Daemon mode for the scheduler
- [ ] Web-based monitoring dashboard

---

## License

[MIT](LICENSE)

---

<div align="center">
  <sub>Built with Python · Maintained by <a href="https://github.com/Batu1-1an">Batu1-1an</a></sub>
</div>
