# Project Context Memory

This document provides a comprehensive overview of the Python Backup & Restoration Tool project. It serves as a central reference to help maintain context across development sessions.

## Project Overview

The Python Backup & Restoration Tool is a command-line utility designed to:
- Back up specified files and directories from Windows and Linux servers to network shares (SMB/NFS)
- Schedule automated backups on a daily or weekly basis
- Provide functionality for manually restoring files from backups
- Work cross-platform (Windows and Linux)
- Handle various network protocols (SMB/NFS)
- Maintain detailed logs of all operations

## Key Components

1. **Configuration System**: YAML-based configuration for sources, destinations, schedules, and logging
2. **Network Connectivity**: Abstraction layer for connecting to SMB and NFS shares
3. **Backup Engine**: Logic for traversing, copying, and verifying files
4. **Restore Engine**: Logic for selecting and recovering files from backups
5. **Scheduler**: System for running backups on configured schedules
6. **Command-Line Interface**: User interface for triggering manual operations
7. **Logging System**: Comprehensive logging for operations and troubleshooting

## Key Decisions

1. **Configuration Format**: Using YAML for human-readable configuration
2. **Network Abstraction**: Implementing an adapter pattern to handle different protocols
3. **Scheduling Library**: Using the `schedule` library for Python-based scheduling
4. **Path Handling**: Using `pathlib` for cross-platform path operations
5. **Error Handling**: Implementing granular error handling that allows partial success
6. **Large File Support**: Using chunked reading/writing for handling large files
7. **Cross-Platform Design**: Isolating OS-specific code into dedicated modules

## Current Development Status

The project has completed most of the core functionality outlined in Sprint 1, including:
- Configuration system with environment variable expansion.
- Basic network share connectivity (SMB/NFS).
- Core backup logic with progress reporting and improved error handling.
- CLI implementation for manual backup and restore operations.
- Unit tests for configuration, network, backup, and restore modules.

Initial work has begun on the restore functionality (part of Sprint 3), including basic conflict handling.

Development has also started on Sprint 2 features, specifically enhancing logging with a placeholder for error notifications in the scheduler.

Refer to `tasks/active_context.md` for the current sprint details and active tasks.

## Key Challenges

1. **Cross-Platform Compatibility**: Ensuring the tool works consistently on both Windows and Linux
2. **Network Protocol Support**: Implementing robust support for both SMB and NFS
3. **Error Handling**: Developing strategies for handling network interruptions and other failures
4. **Large File Support**: Efficiently handling very large files without memory issues
5. **Security**: Managing credentials and permissions securely
6. **Scheduling**: Ensuring scheduled backups run reliably, even after system restarts

## Technical Debt Tracking

1. **SMB Protocol Version Handling**: Need to implement better handling of different SMB protocol versions
2. **Error Recovery**: Enhance recovery from network interruptions during file transfers
3. **Configuration Validation**: Improve validation for more complex configuration scenarios
4. **Testing Coverage**: Expand test coverage, particularly for edge cases
5. **Metadata Preservation**: Review and refine metadata preservation during backup/restore.

## Future Enhancements

1. **Incremental Backups**: Add support for incremental backups to improve efficiency
2. **Compression**: Implement optional compression for backup files
3. **Encryption**: Add support for encrypting sensitive backups
4. **Web Interface**: Consider adding a web-based user interface for monitoring and management
5. **Remote Management**: Allow for remote management of backup operations
6. **Multiple Destinations**: Support backing up to multiple destinations for redundancy
7. **Backup Rotation and Pruning**: Implement policies for managing old backups.
8. **Daemon Mode**: Implement a robust daemon mode for the scheduler.
9. **Error Notification Implementation**: Replace placeholder with actual notification methods (e.g., email).

## Implementation Patterns

1. **Factory Pattern**: Used for creating appropriate network share connections
2. **Strategy Pattern**: Used for different backup/restore strategies
3. **Adapter Pattern**: Used for abstracting OS-specific operations
4. **Command Pattern**: Used in the CLI implementation
5. **Observer Pattern**: Used for progress monitoring during operations

## Related Documentation

- **Architecture**: See `docs/architecture.md` for system design details
- **Requirements**: See `docs/product_requirement_docs.md` for user stories and requirements
- **Technical Details**: See `docs/technical.md` for implementation specifics
- **Project Plan**: See `docs/backup_tool_plan.md` for the overall project plan
- **Directory Structure**: See `docs/directory_structure.md` for codebase organization
- **Lessons Learned**: See `docs/lessons_learned.md` for accumulated project intelligence
- **Error Documentation**: See `docs/error_documentation.md` for solutions to common issues