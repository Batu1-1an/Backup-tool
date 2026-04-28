import os
import time
import schedule
import logging

from . import config
from . import backup

logger = logging.getLogger("backup_tool")

def send_error_notification(error_message):
    """
    Placeholder function to send an error notification.
    This should be implemented with actual notification logic (e.g., email, SMS, push notification).

    Args:
        error_message (str): The error message to include in the notification.
    """
    logger.error(f"Sending error notification: {error_message}")
    # TODO: Implement actual error notification logic here (e.g., send email, call API)
    pass # Placeholder implementation

def run_scheduled_backups(config_path):
    """
    Loads the configuration and sets up scheduled backup jobs.

    Args:
        config_path (str): The path to the configuration file.
    """
    logger.info(f"Starting scheduler with config: {config_path}")

    try:
        config_data = config.load_config(config_path)
        schedule_config = config_data.get("schedule")

        if not schedule_config:
            logger.warning("No schedule found in configuration. Scheduler will not run any jobs.")
            return

        # Setup daily schedule
        if "daily" in schedule_config:
            daily_time = schedule_config["daily"]
            try:
                # Validate time format (basic check)
                time.strptime(daily_time, "%H:%M")
                schedule.every().day.at(daily_time).do(
                    run_backup_job, config_data=config_data
                )
                logger.info(f"Scheduled daily backup at {daily_time}")
            except ValueError:
                logger.error(f"Invalid daily schedule time format: {daily_time}. Expected HH:MM.")
            except Exception as e:
                 logger.error(f"Error scheduling daily backup: {e}")


        # Setup weekly schedule
        if "weekly" in schedule_config:
            weekly_schedule = schedule_config["weekly"]
            try:
                # Expected format: "Day HH:MM" (e.g., "Sunday 03:00")
                parts = weekly_schedule.split()
                if len(parts) == 2:
                    day_of_week = parts[0].lower()
                    weekly_time = parts[1]

                    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    if day_of_week in valid_days:
                         time.strptime(weekly_time, "%H:%M") # Validate time format

                         if day_of_week == "monday":
                             schedule.every().monday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "tuesday":
                             schedule.every().tuesday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "wednesday":
                             schedule.every().wednesday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "thursday":
                             schedule.every().thursday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "friday":
                             schedule.every().friday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "saturday":
                             schedule.every().saturday.at(weekly_time).do(run_backup_job, config_data=config_data)
                         elif day_of_week == "sunday":
                             schedule.every().sunday.at(weekly_time).do(run_backup_job, config_data=config_data)

                         logger.info(f"Scheduled weekly backup on {day_of_week.capitalize()} at {weekly_time}")
                    else:
                        logger.error(f"Invalid day of week in weekly schedule: {weekly_schedule}. Expected format 'Day HH:MM'.")
                else:
                    logger.error(f"Invalid weekly schedule format: {weekly_schedule}. Expected format 'Day HH:MM'.")
            except ValueError:
                logger.error(f"Invalid weekly schedule time format: {weekly_schedule}. Expected HH:MM.")
            except Exception as e:
                 logger.error(f"Error scheduling weekly backup: {e}")


        # Add other schedule types (e.g., hourly, monthly) here if needed

        if not schedule.get_jobs():
            logger.warning("No valid schedules were configured. Scheduler is running but has no jobs.")

        # Keep the script running to execute scheduled jobs
        while True:
            schedule.run_pending()
            time.sleep(1)

    except config.ConfigError as e:
        logger.error(f"Configuration error while setting up scheduler: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the scheduler: {e}")


def run_backup_job(config_data):
    """
    Wrapper function to run a backup and handle potential errors for the scheduler.
    """
    logger.info("Running scheduled backup job...")
    try:
        backup.perform_backup(config_data)
        logger.info("Scheduled backup job completed successfully.")
    except Exception as e:
        error_message = f"Scheduled backup job failed: {e}"
        logger.error(error_message)
        send_error_notification(error_message) # Call the notification function

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Assuming logging is already set up
    # from logger import setup_logging; setup_logging()

    # Create a dummy config file for testing
    dummy_config_content = """
backup_sources:
  - /fake/source1

backup_target:
  path: //fake_server/fake_share
  type: smb

schedule:
  daily: "23:59" # Schedule for almost immediately for testing
  # weekly: "Sunday 03:00"
"""
    dummy_config_path = "test_scheduler_config.yaml"
    with open(dummy_config_path, "w") as f:
        f.write(dummy_config_content)

    print(f"Running scheduler with dummy config (will attempt backup at 23:59 and likely fail due to network placeholders)...")
    try:
        # In a real scenario, this would run indefinitely
        # For testing, you might want to limit the runtime or manually trigger
        run_scheduled_backups(dummy_config_path)
    except Exception as e:
        print(f"Scheduler stopped due to an error: {e}")
    finally:
        # Clean up the dummy config file
        if os.path.exists(dummy_config_path):
            os.remove(dummy_config_path)