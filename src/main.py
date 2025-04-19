import argparse
import sys
import logging
import os

# Import modules from the backup_tool package
from backup_tool import config, logger, backup, restore, scheduler, network

def main():
    parser = argparse.ArgumentParser(description="Python Backup & Restoration Tool")

    # Add arguments for different commands (backup, restore, schedule)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common argument for config file
    parser.add_argument("--config", default="config/backup_config.yaml", help="Path to the configuration file (default: config/backup_config.yaml)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Set the logging level (default: INFO)")
    parser.add_argument("--log-file", help="Path to the log file (overrides config)")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Run a manual backup")
    backup_parser.add_argument("--source", nargs='+', help="Specific source(s) to backup (overrides config)")
    # Implementing a full target override via a single CLI argument is complex.
    # Consider using a separate override config file or environment variables for target overrides.
    # backup_parser.add_argument("--target", help="Specific target destination (overrides config)") # TODO: Implement overrides

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Run a manual restore")
    restore_parser.add_argument("--backup-timestamp", required=True, help="Timestamp of the backup to restore from (YYYYMMDD_HHMMSS)")
    restore_parser.add_argument("--destination", required=True, help="Destination path to restore to")
    restore_parser.add_argument("--conflict-strategy", default="overwrite", choices=["overwrite", "error"], help="Strategy for handling existing destination (default: overwrite)")

    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Run the scheduler")

    args = parser.parse_args()

    # --- Setup Logging ---
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_level_map.get(args.log_level.upper(), logging.INFO)
    log_file = args.log_file # Use command-line arg if provided

    # Load config to potentially get log file path if not provided via args
    config_data = None
    try:
        # Check if config file exists before trying to load it for logging path
        if os.path.exists(args.config):
            config_data = config.load_config(args.config)
            if not log_file and config_data.get("logging", {}).get("log_file"):
                log_file = config_data["logging"]["log_file"]
        else:
            # If config doesn't exist, use default log path unless overridden by args
            if not log_file:
                 log_file = "backup_tool.log" # Default log file name
            print(f"Warning: Configuration file '{args.config}' not found. Using default logging settings.", file=sys.stderr)

        logger.setup_logging(log_file_path=log_file, level=log_level)
        log = logging.getLogger("backup_tool") # Get the logger instance

    except config.ConfigError as e:
        print(f"Configuration Error during logging setup: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up logging: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Load Configuration (if not already loaded) ---
    try:
        if config_data is None: # Load only if not loaded during logging setup
             log.info(f"Loading configuration from: {args.config}")
             config_data = config.load_config(args.config)
             log.info("Configuration loaded successfully.")
    except config.ConfigError as e:
        log.error(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"Failed to load configuration: {e}")
        sys.exit(1)


    # --- Execute Command ---
    try:
        if args.command == "backup":
            log.info("Executing manual backup command...")
            # Pass source override if provided
            backup.perform_backup(config_data, source_override=args.source)
            log.info("Manual backup completed successfully.")
        elif args.command == "restore":
            log.info("Executing manual restore command...")
            restore.perform_restore(config_data, args.backup_timestamp, args.destination, conflict_strategy=args.conflict_strategy)
            log.info("Manual restore completed successfully.")
        elif args.command == "schedule":
            log.info("Starting scheduler...")
            # The scheduler function runs indefinitely
            scheduler.run_scheduled_backups(args.config) # Pass config path, scheduler reloads it
        else:
            parser.print_help()
            sys.exit(0) # Exit normally after printing help

    except config.ConfigError as e:
        log.error(f"Configuration Error: {e}")
        sys.exit(1)
    except network.NetworkError as e:
        log.error(f"Network Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        log.error(f"File Not Found Error: {e}")
        sys.exit(1)
    except NotImplementedError as e:
         log.error(f"Functionality not implemented: {e}")
         sys.exit(1)
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}", exc_info=True) # Log traceback
        sys.exit(1)

    sys.exit(0) # Success


if __name__ == "__main__":
    main()