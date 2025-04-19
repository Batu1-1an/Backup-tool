# Architecture Documentation

This document outlines the system architecture for the Python Backup & Restoration Tool.

## Overview

The Python Backup & Restoration Tool is designed with a modular architecture that separates concerns into distinct components. It follows a command-line interface pattern with separate modules handling different aspects of the backup and restoration process. The tool is built to be cross-platform (Windows and Linux) and supports backing up to network shares (SMB/NFS).

## Components

### Core Components

1.  **CLI Interface (`main.py`)** - Entry point for user interaction that processes command-line arguments (including backup source override and restore conflict strategy) and routes to appropriate functionality.
2.  **Configuration Manager (`config.py`)** - Handles loading, parsing, and validating the YAML configuration file that defines backup sources, targets, schedules, and retention policies.
3.  **Backup Module (`backup.py`)** - Implements the core backup logic, including file copying (with progress), directory traversal, handling of file metadata, backup rotation/pruning, and initial support for incremental backups (comparing against the latest backup).
4.  **Restore Module (`restore.py`)** - Implements the restoration logic to recover files from backups to their original or alternative locations, including basic conflict handling (overwrite/error).
5.  **Scheduler (`scheduler.py`)** - Manages the scheduling of automated backups based on the configuration file and includes placeholders for error notifications.
6.  **Network Module (`network.py`)** - Abstracts the connectivity to different network share types (SMB/NFS) and handles OS-specific implementations.
7.  **Logger (`logger.py`)** - Provides centralized logging functionality with rotation for all components.

### External Dependencies

1.  **PyYAML** - Used for parsing the YAML configuration files.
2.  **schedule** - Used for implementing the backup scheduling functionality.

## System Interaction Diagram

```mermaid
graph TD
    subgraph User Interaction
        U[User/OS Scheduler] --> CLI{CLI Interface};
    end

    subgraph Core Logic
        CLI --> CfgLdr[Config Manager];
        CLI -- Manual Backup --> BkpMod[Backup Module];
        CLI -- Manual Restore --> RstMod[Restore Module];
        CLI -- Run Scheduler --> SchedMod[Scheduler];
        SchedMod -- Trigger Backup --> BkpMod;

        BkpMod --> NetMod[Network Module];
        RstMod --> NetMod;

        NetMod --> NS[Network Share (SMB/NFS)];
        BkpMod --> FS_Src[Source Filesystem];
        RstMod --> FS_Dest[Destination Filesystem];

        CfgLdr --> LogMod[Logger];
        BkpMod --> LogMod;
        RstMod --> LogMod;
        SchedMod --> LogMod;
        NetMod --> LogMod;
    end

    subgraph External Systems
        LogMod --> LogFile[Log File];
        FS_Src --> BkpMod;
        NetMod --> NS;
        NS --> NetMod;
        RstMod --> FS_Dest;
    end
```

## Data Flow

1.  **Configuration Initialization**:
    *   System loads YAML configuration file via `main.py` using `config.py`.
    *   Validates paths, schedules, network share settings, and retention policies.
    *   Initializes the logger (`logger.py`) with configured settings.

2.  **Backup Process**:
    *   Triggered manually via CLI (`main.py`) or by scheduler (`scheduler.py`).
    *   Connects to configured network share using `network.py`.
    *   (Incremental Only) Finds the latest backup using `backup.py`.
    *   Traverses source directories/files (`backup.py`).
    *   Creates backup structure on target with timestamp (`backup.py`).
    *   Copies files (full or incrementally based on comparison with latest backup) with metadata preservation when possible (`backup.py`).
    *   Logs each operation's status using `logger.py`.
    *   Performs backup rotation and pruning based on retention policy (`backup.py`).

3.  **Restore Process**:
    *   Triggered manually via CLI (`main.py`).
    *   User selects a backup set to restore from (timestamp provided via CLI).
    *   Connects to configured network share using `network.py`.
    *   Copies files from backup to original or alternate location (`restore.py`).
    *   Handles conflicts according to configuration (overwrite/error) (`restore.py`).
    *   Logs the restoration process using `logger.py`.

## Cross-Platform Considerations

The architecture handles platform differences through:

1.  **Path Abstraction** - Using `os.path` for OS-agnostic path handling (Note: `pathlib` could be considered for future refactoring).
2.  **Network Protocol Adapters** - Different implementations for Windows/Linux SMB/NFS connectivity within `network.py`.
3.  **Filesystem Operations** - Handling differences in file permissions, attributes, and symlinks (basic implementation, needs further refinement).

## Error Handling Strategy

Error handling is implemented at multiple levels:

1.  **Component-level** - Each module handles its domain-specific errors (e.g., `BackupError`, `RestoreError`, `NetworkError`, `ConfigError`).
2.  **Cross-cutting** - Global exception handlers in `main.py` for unexpected errors.
3.  **Recovery** - Partial backup/restore capabilities (continue on error for individual files/sources) to handle transient network issues or file access problems. Error notification placeholder added to scheduler.

---

**Development Progress Note:** The architecture described here is largely implemented. Recent additions include backup rotation/pruning logic and initial structures for incremental backups within the Backup Module, conflict handling in the Restore Module, and CLI argument updates. Error notification placeholders have been added to the Scheduler.