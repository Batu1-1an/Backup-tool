# Usage Documentation

This document provides detailed instructions for using the Python Backup & Restoration Tool.

## Installation

### Prerequisites

- Python 3.7 or higher
- Network access to the target share (SMB or NFS)
- Appropriate permissions for source files and destination share

### Installing from Source

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd backup_tool
   ```

2. (Optional) Create a virtual environment:
   ```bash
   # On Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Configuration

The backup tool uses a YAML configuration file. By default, it looks for `config/backup_config.yaml`, but you can specify a different path using the `--config` option.

### Basic Configuration Example

```yaml
# --- Backup Sources ---
backup_sources:
  - /var/log/syslog
  - /etc/nginx/nginx.conf
  - /home/user/documents

# --- Backup Target ---
backup_target:
  path: //backup_server/backup_share
  type: smb
  credentials:
    username: YOUR_BACKUP_USER
    password: YOUR_BACKUP_PASSWORD

# --- Schedule ---
schedule:
  daily: "02:00"
  weekly: "Sunday 03:00"

# --- Logging ---
logging:
  log_file: /var/log/backup_tool/backup_tool.log
  level: INFO
```

### Configuration Sections

#### Backup Sources

List the directories and files you want to back up:

```yaml
backup_sources:
  - /path/to/directory
  - /path/to/file.txt
  # Windows paths
  - C:\Users\Administrator\Documents
  - D:\Data\important.xlsx
```

#### Backup Target

Configure the network share where backups will be stored:

```yaml
backup_target:
  # For SMB: Use Windows-style paths
  path: //server/share
  type: smb
  # Optional: Credentials
  credentials:
    username: YOUR_USERNAME
    password: YOUR_PASSWORD
    domain: optional_domain

  # For NFS:
  # path: server:/export/path
  # type: nfs
```

> **Security Note**: For improved security, consider using environment variables for sensitive information:
>
> ```yaml
> credentials:
>   username: ${BACKUP_USER}
>   password: ${BACKUP_PASS}
> ```

#### Schedule

Define the backup schedule (daily and/or weekly):

```yaml
schedule:
  daily: "02:00"  # Run daily backup at 2:00 AM
  weekly: "Sunday 03:00"  # Run weekly backup on Sunday at a 3:00 AM
```

#### Logging

Configure logging settings:

```yaml
logging:
  log_file: /var/log/backup_tool.log  # or C:\Logs\backup_tool.log on Windows
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  max_bytes: 10485760  # 10MB
  backup_count: 5  # Keep 5 rotated log files
```

## Command Line Usage

### Backup Command

Run a manual backup:

```bash
backup_tool backup
```

Options:
- `-c, --config PATH`: Path to configuration file (default: `./config/backup_config.yaml`)
- `-f, --force`: Force backup even if last backup is recent

Examples:
```bash
# Run backup with default configuration
backup_tool backup

# Run backup with a specific configuration file
backup_tool backup -c /path/to/custom-config.yaml

# Force a backup regardless of timing
backup_tool backup --force
```

### Restore Command

Restore files from a backup:

```bash
backup_tool restore
```

Options:
- `-c, --config PATH`: Path to configuration file
- `-b, --backup TEXT`: Specific backup timestamp to restore from (if not specified, lists available backups)
- `-d, --dest PATH`: Alternative destination path for restored files
- `--conflict [skip|overwrite|prompt]`: How to handle conflicts (default: prompt)

Examples:
```bash
# List available backups
backup_tool restore

# Restore a specific backup
backup_tool restore -b 20230315-020000

# Restore to an alternative location
backup_tool restore -b 20230315-020000 -d /path/to/restore/location

# Restore and overwrite any existing files
backup_tool restore -b 20230315-020000 --conflict overwrite
```

### Scheduler Command

Run the scheduler for automated backups:

```bash
backup_tool run
```

Options:
- `-c, --config PATH`: Path to configuration file
- `--foreground`: Run in the foreground instead of as a daemon

Examples:
```bash
# Run scheduler as a daemon
backup_tool run

# Run scheduler in the foreground
backup_tool run --foreground
```

### Validate Command

Validate the configuration file:

```bash
backup_tool validate
```

Options:
- `-c, --config PATH`: Path to configuration file to validate

Examples:
```bash
# Validate the default configuration
backup_tool validate

# Validate a specific configuration file
backup_tool validate -c /path/to/custom-config.yaml
```

## Common Workflows

### Initial Setup

1. Install the tool
2. Copy and modify the example configuration:
   ```bash
   cp config/backup_config.yaml.example config/backup_config.yaml
   ```
3. Edit the configuration with your backup sources and destination
4. Validate the configuration:
   ```bash
   backup_tool validate
   ```
5. Run a test backup:
   ```bash
   backup_tool backup
   ```

### Scheduling Regular Backups

To set up scheduled backups:

1. Configure the schedule in your configuration file
2. Run the scheduler:
   ```bash
   backup_tool run
   ```
3. (Optional) Set up your system to run the scheduler at startup:
   - On Linux: Add to systemd or crontab
   - On Windows: Create a scheduled task

### Restoring Files

To restore files from a backup:

1. List available backups:
   ```bash
   backup_tool restore
   ```
2. Select a backup to restore:
   ```bash
   backup_tool restore -b <timestamp>
   ```
3. Follow the prompts to confirm restoration

## Troubleshooting

### Common Issues

#### Connection Errors

If you encounter connection errors to the network share:

1. Verify network connectivity to the share
2. Check credentials in the configuration
3. Ensure appropriate network protocols are enabled
4. Check firewall settings

#### Permission Errors

If you encounter permission errors:

1. Verify the running user has read access to source files
2. Verify credentials have write access to the backup destination
3. Check file and directory permissions

#### Scheduling Issues

If scheduled backups are not running:

1. Verify the scheduler is running:
   ```bash
   ps aux | grep backup_tool  # On Linux
   Get-Process | Where-Object { $_.Name -like "*backup_tool*" }  # On Windows
   ```
2. Check the log file for errors
3. Verify the system time is correct
4. Ensure the system is not going to sleep/hibernate during scheduled times

### Log File Analysis

The log file contains detailed information about operations. Look for entries with ERROR level to identify issues:

```
2023-03-15 02:00:00 INFO: Starting backup operation
2023-03-15 02:00:01 INFO: Connected to network share
2023-03-15 02:00:05 ERROR: Failed to access file /path/to/file: Permission denied
```

## Advanced Usage

### Environment Variables

You can use environment variables in the configuration file for sensitive information or environment-specific settings:

```yaml
backup_target:
  path: ${BACKUP_SHARE_PATH}
  credentials:
    username: ${BACKUP_USER}
    password: ${BACKUP_PASS}
```

Set the environment variables before running the tool:

```bash
# Linux/macOS
export BACKUP_SHARE_PATH="//server/share"
export BACKUP_USER="YOUR_USER"
export BACKUP_PASS="YOUR_PASSWORD"

# Windows
$env:BACKUP_SHARE_PATH="\\server\share"
$env:BACKUP_USER="YOUR_USER"
$env:BACKUP_PASS="YOUR_PASSWORD"
```

### Running as a Service

#### On Linux (systemd)

Create a systemd service file:

```ini
[Unit]
Description=Backup Tool Scheduler
After=network.target

[Service]
Type=simple
User=backup
ExecStart=/path/to/venv/bin/backup_tool run --config /etc/backup_tool/config.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Install and enable the service:

```bash
sudo cp backup_tool.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable backup_tool
sudo systemctl start backup_tool
```

#### On Windows (Task Scheduler)

Create a scheduled task to run at system startup:

1. Open Task Scheduler
2. Create a new task
3. Set it to run at system startup
4. Set the action to:
   - Program: `C:\path\to\python.exe`
   - Arguments: `-m backup_tool run --config C:\path\to\config.yaml` 