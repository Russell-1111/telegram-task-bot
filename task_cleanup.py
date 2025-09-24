# Open task_cleanup.py

import outlook_api
from datetime import datetime, timedelta, timezone # Need timedelta for date comparison
import logging
import sys # To allow logging to console as well
import pytz

# --- Setup Logging for Cleanup Script ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout) # Also log to console
    ]
)
logger = logging.getLogger(__name__)

def cleanup_old_tasks():
    logger.info("Starting cleanup of old Outlook tasks...")
    
    # Add this debug info
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    today_malaysia = datetime.now(malaysia_tz).date()
    logger.info(f"Today in Malaysia timezone: {today_malaysia}")

    # 1. Get Authentication Token
    access_token = None
    try:
        access_token = outlook_api.get_auth_token()
        logger.info("Successfully authenticated with Outlook!")
        
    except Exception as e:
        logger.error(f"Authentication failed for cleanup script: {e}")
        print(f"ERROR: Could not authenticate for Outlook cleanup. Please try again. Details: {e}")
        return

    if not access_token:
        logger.error("No access token obtained. Cannot proceed with cleanup.")
        return

    # 2. Get all tasks
    all_tasks = []
    try:
        all_tasks = outlook_api.get_all_tasks(access_token)
        logger.info(f"Found {len(all_tasks)} tasks in total.")
    except Exception as e:
        logger.error(f"Failed to retrieve tasks: {e}")
        print(f"ERROR: Failed to retrieve tasks. Cleanup aborted. Details: {e}")
        return

    # 3. Determine the "cutoff" date
    # We want to delete tasks whose due date is *yesterday* or earlier.
    # So, the cutoff is the start of *today*. Anything before that is old.
    # Example: If today is Sept 22, 2025, tasks due Sept 21 or earlier are old.
    
    # Define the Malaysia timezone
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')

    # If a task's due date is BEFORE today_malaysia, it's old.
    today_malaysia = datetime.now(malaysia_tz).date()
   
    deleted_count = 0
    # 4. Loop through each task and check its due date
    for task in all_tasks:
        task_title = task.get("title", "No Title")
        task_id = task.get("id")
        due_date_time_obj = task.get("dueDateTime")

        if not task_id:
            logger.warning(f"Task '{task_title}' has no ID, skipping.")
            continue

        if due_date_time_obj and due_date_time_obj.get("dateTime"):
            try:
                task_due_date_str = due_date_time_obj["dateTime"]
                api_timezone_str = due_date_time_obj.get("timeZone", "UTC")
                
                # Convert API timezone string to pytz timezone
                if api_timezone_str == "UTC":
                    api_timezone = timezone.utc
                else:
                    try:
                        api_timezone = pytz.timezone(api_timezone_str)
                    except:
                        # Fallback to UTC if timezone is unrecognized
                        api_timezone = timezone.utc
                        logger.warning(f"Unknown timezone '{api_timezone_str}', using UTC")
                
                # Parse the datetime and set the correct timezone
                task_due_datetime = datetime.fromisoformat(task_due_date_str.replace('Z', ''))
                
                # If the datetime is naive (no timezone), add the API's timezone
                if task_due_datetime.tzinfo is None:
                    task_due_datetime = task_due_datetime.replace(tzinfo=api_timezone)
                
                # Convert to Malaysia timezone
                task_due_date_malaysia = task_due_datetime.astimezone(malaysia_tz).date()
                
                logger.info(f"Task '{task_title}' - Original: {task_due_date_str} ({api_timezone_str}) -> Malaysia: {task_due_date_malaysia}")
                
                # Compare the task's due date (just the date part) with today's date in Malaysia tiemezone
                if task_due_date_malaysia < today_malaysia:
                    logger.info(f"Task '{task_title}' (ID: {task_id}) is old (due: {task_due_date_malaysia}), attempting to delete.")
                    try:
                        outlook_api.delete_task(access_token, task_id)
                        deleted_count += 1
                    except Exception as delete_error:
                        logger.error(f"Failed to delete task '{task_title}' (ID: {task_id}): {delete_error}")
                else:
                    logger.debug(f"Task '{task_title}' (ID: {task_id}) is not old (due: {task_due_date_malaysia}). Skipping.")

            except ValueError:
                logger.warning(f"Task '{task_title}' (ID: {task_id}) has an invalid due date format: {task_due_date_str}. Skipping date check.")
            except Exception as e:
                logger.error(f"Error processing task '{task_title}' (ID: {task_id}): {e}")
        else:
            logger.debug(f"Task '{task_title}' (ID: {task_id}) has no due date. Skipping.")
    
    logger.info(f"Cleanup complete. Deleted {deleted_count} old tasks.")

# This makes sure cleanup_old_tasks() runs when you execute this script
if __name__ == "__main__":
    cleanup_old_tasks()