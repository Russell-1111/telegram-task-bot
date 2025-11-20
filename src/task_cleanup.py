"""
Task Cleanup Script - Refactored to Use Service Layer

This script deletes old Outlook tasks (tasks with due dates before today)
using the new service layer architecture introduced in Phase 3.

Changes from legacy version:
- Uses OutlookService instead of direct outlook_api calls
- Uses TokenManager for centralized token management
- Consistent with main bot architecture
- Improved error handling and logging

Usage:
    python src/task_cleanup.py
"""

import sys
import os
from datetime import datetime, timezone
import logging
import pytz

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import new service layer (Phase 3 architecture)
import asyncio
from services import OutlookService
from utils import TokenManager

# --- Setup Logging for Cleanup Script ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console
    ]
)
logger = logging.getLogger(__name__)

async def cleanup_old_tasks():
    """
    Delete old Outlook tasks (tasks with due dates before today).
    
    Uses Phase 3 service layer architecture:
    - OutlookService for API operations
    - TokenManager for token management
    - Consistent error handling
    
    Returns:
        int: Number of tasks deleted, or -1 if cleanup failed
    """
    logger.info("=" * 60)
    logger.info("Starting cleanup of old Outlook tasks...")
    logger.info("=" * 60)
    
    # Define Malaysia timezone for date comparisons
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    today_malaysia = datetime.now(malaysia_tz).date()
    logger.info(f"Today in Malaysia timezone: {today_malaysia}")
    
    # Initialize service layer components
    outlook_service = OutlookService()
    token_manager = TokenManager()
    
    # 1. Authenticate with Outlook using OutlookService
    access_token = None
    try:
        logger.info("Initiating Outlook authentication...")
        access_token = await outlook_service.authenticate()
        # Use a dummy user_id (0) for standalone script
        token_manager.set_token(user_id=0, token=access_token)
        logger.info("✅ Successfully authenticated with Outlook!")
        
    except Exception as e:
        logger.error(f"❌ Authentication failed for cleanup script: {e}")
        print(f"\nERROR: Could not authenticate for Outlook cleanup.")
        print(f"Details: {e}")
        print("Please ensure you have network connectivity and valid credentials.\n")
        return -1

    if not access_token:
        logger.error("No access token obtained. Cannot proceed with cleanup.")
        return -1

    # 2. Get all tasks using OutlookService
    all_tasks = []
    try:
        logger.info("Fetching all tasks from Outlook...")
        all_tasks = await outlook_service.get_all_tasks(access_token)
        logger.info(f"✅ Found {len(all_tasks)} tasks in total.")
    except Exception as e:
        logger.error(f"❌ Failed to retrieve tasks: {e}")
        print(f"\nERROR: Failed to retrieve tasks. Cleanup aborted.")
        print(f"Details: {e}\n")
        return -1

    # 3. Process tasks and delete old ones
    # A task is "old" if its due date is before today (Malaysia timezone)
    # Example: If today is Oct 3, 2025, tasks due Oct 2 or earlier are old.
    
    deleted_count = 0
    skipped_count = 0
    error_count = 0
    
    logger.info("-" * 60)
    logger.info("Processing tasks...")
    logger.info("-" * 60)
    
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
                
                # Compare the task's due date (just the date part) with today's date in Malaysia timezone
                if task_due_date_malaysia < today_malaysia:
                    logger.info(f"🗑️  Task '{task_title}' (ID: {task_id}) is old (due: {task_due_date_malaysia}), attempting to delete.")
                    try:
                        await outlook_service.delete_task(access_token, task_id)
                        deleted_count += 1
                        logger.info(f"   ✅ Deleted successfully")
                    except Exception as delete_error:
                        logger.error(f"   ❌ Failed to delete: {delete_error}")
                        error_count += 1
                else:
                    logger.debug(f"⏭️  Task '{task_title}' (ID: {task_id}) is not old (due: {task_due_date_malaysia}). Skipping.")
                    skipped_count += 1

            except ValueError as ve:
                logger.warning(f"⚠️  Task '{task_title}' (ID: {task_id}) has invalid due date format: {task_due_date_str}. Skipping.")
                skipped_count += 1
            except Exception as e:
                logger.error(f"❌ Error processing task '{task_title}' (ID: {task_id}): {e}")
                error_count += 1
        else:
            logger.debug(f"⏭️  Task '{task_title}' (ID: {task_id}) has no due date. Skipping.")
            skipped_count += 1
    
    # 5. Print summary
    logger.info("=" * 60)
    logger.info("CLEANUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total tasks processed:   {len(all_tasks)}")
    logger.info(f"Tasks deleted:           {deleted_count} ✅")
    logger.info(f"Tasks skipped:           {skipped_count} ⏭️")
    logger.info(f"Errors encountered:      {error_count} ❌")
    logger.info("=" * 60)
    
    if deleted_count > 0:
        logger.info(f"✅ Cleanup complete! Successfully deleted {deleted_count} old task(s).")
    else:
        logger.info("✅ Cleanup complete! No old tasks found to delete.")
    
    return deleted_count

def main():
    """
    Main entry point for task cleanup script.
    
    Provides user-friendly console output and proper exit codes.
    """
    print("\n" + "=" * 60)
    print("🧹 OUTLOOK TASK CLEANUP UTILITY")
    print("=" * 60)
    print("This script will delete tasks with due dates before today.")
    print("Using Phase 3 Service Layer Architecture")
    print("=" * 60 + "\n")
    
    try:
        deleted_count = asyncio.run(cleanup_old_tasks())
        
        if deleted_count == -1:
            print("\n❌ Cleanup failed. Check logs above for details.\n")
            sys.exit(1)
        elif deleted_count == 0:
            print("\n✅ No old tasks to delete. Your task list is up to date!\n")
            sys.exit(0)
        else:
            print(f"\n✅ Successfully deleted {deleted_count} old task(s)!\n")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup cancelled by user.\n")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Unexpected error in cleanup script: {e}", exc_info=True)
        print(f"\n❌ CRITICAL ERROR: {e}")
        print("See logs above for full stack trace.\n")
        sys.exit(1)


# This makes sure main() runs when you execute this script
if __name__ == "__main__":
    main()