"""
Message handlers for Telegram bot regular messages.

This module handles:
- echo() function: Processes user messages for task creation/updates
- LLM integration for intent detection
- Task creation in Outlook
- Due date updates for existing tasks
"""

import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import pytz

# Import from sibling modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import outlook_api
from config import config
from services import LLMService
from validators import TaskValidator
from formatters import validate_and_process_date, format_due_date_for_outlook

logger = logging.getLogger(__name__)

# Malaysia timezone for consistent date handling
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# Initialize LLM service and task validator
llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
task_validator = TaskValidator()

# Dictionary to store user's last created task for updates
# Format: {user_id: {"id": task_id, "title": task_title, "due_date": due_date, "created_at": datetime}}
user_last_tasks = {}


def store_user_last_task(user_id, task_id, task_title, due_date=None):
    """
    Store the user's last created task for potential due date updates.
    
    Args:
        user_id (int): Telegram user ID
        task_id (str): Outlook task ID
        task_title (str): Task title/summary
        due_date (str): Due date in YYYY-MM-DD format (optional)
    """
    user_last_tasks[user_id] = {
        "id": task_id,
        "title": task_title, 
        "due_date": due_date,
        "created_at": datetime.now(MALAYSIA_TZ)
    }
    logger.info(f"Stored last task for user {user_id}: {task_title}")


def get_user_last_task(user_id):
    """
    Get the user's last created task.
    
    Args:
        user_id (int): Telegram user ID
    
    Returns:
        dict: Task info with keys: id, title, due_date, created_at
              None if no task found
    """
    return user_last_tasks.get(user_id, None)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process user messages for task creation and due date updates.
    
    Features:
    - LLM-powered intent detection (create_task, update_due_date, unknown)
    - Task summary validation (3-12 words)
    - Fallback summary generation for invalid LLM outputs
    - Date parsing and validation (Malaysia timezone)
    - Outlook task creation with due dates
    - Due date updates for existing tasks
    - Comprehensive error handling and user feedback
    
    Workflow:
    1. Receive user message
    2. Send to LLM service for intent analysis
    3. Validate task summary (if creating task)
    4. Process due date (if provided)
    5. Call Outlook API (create or update)
    6. Store task info for future updates
    7. Send confirmation to user
    
    Args:
        update (Update): Telegram update object containing user message
        context (ContextTypes.DEFAULT_TYPE): Telegram context object
    
    Returns:
        None (sends messages via Telegram API)
    
    Intent Handling:
        - create_task: Creates new task in Outlook with optional due date
        - update_due_date: Updates due date of user's last created task
        - unknown: Provides helpful guidance on how to use the bot
    
    Example:
        User: "Buy groceries tomorrow"
        Bot: ✅ Task created in Outlook: 'Buy groceries and supplies'
             📅 Due: 2024-12-16
        
        User: "Change due date to Friday"
        Bot: ✅ Updated task: 'Buy groceries and supplies'
             📅 New due date: 2024-12-20
    
    Technical Note:
        Uses global outlook_access_token from command_handlers module.
        In production, implement per-user token storage.
    """
    # Import outlook_access_token from command_handlers
    from .command_handlers import get_outlook_token, set_outlook_token
    outlook_access_token = get_outlook_token()
    
    user_message = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Received message from {update.effective_user.first_name}: '{user_message}'")

    if not config.gemini_api_key:
        await update.message.reply_text("Error: Gemini API Key not configured. Please set GEMINI_API_KEY environment variable.")
        logger.error("Gemini API Key is missing.")
        return

    try:
        # Get current date for LLM context
        current_date = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
        
        # Get user's last task for update context
        last_task = get_user_last_task(user_id)
        last_task_context = None
        if last_task:
            last_task_context = {
                'title': last_task['title'],
                'due_date': last_task.get('due_date')
            }
        
        # Analyze user message with LLM service
        task_intent = llm_service.analyze_task_request(
            user_message=user_message,
            current_date=current_date,
            last_task_context=last_task_context
        )
        
        intent = task_intent.intent
        raw_summary = task_intent.summary
        due_date = task_intent.due_date
        
        logger.info(f"LLM Response - Intent: {intent}, Raw Summary: '{raw_summary}', Due Date: {due_date}")
        
        # Validate task summary (only for create_task intent)
        validated_summary = raw_summary
        if intent == "create_task" and raw_summary:
            validation_result = task_validator.validate_summary(raw_summary)
            
            if validation_result.is_valid:
                validated_summary = validation_result.validated_value
                logger.info(f"Valid task summary: '{validated_summary}' ({validation_result.word_count} words)")
            else:
                logger.warning(f"Invalid task summary: {validation_result.message}")
                # Attempt to generate a fallback summary
                validated_summary = task_validator.generate_fallback_summary(user_message)
                fallback_validation = task_validator.validate_summary(validated_summary)
                
                if fallback_validation.is_valid:
                    logger.info(f"Generated valid fallback summary: '{validated_summary}' ({fallback_validation.word_count} words)")
                else:
                    logger.error(f"Fallback summary also invalid: {fallback_validation.message}")
                    # Ultimate fallback - create a minimal valid summary
                    validated_summary = "Complete important task"  # 3 words - minimum valid
                    logger.warning(f"Using emergency fallback summary: '{validated_summary}'")
        
        summary = validated_summary
        
        # Validate and process the due_date
        processed_due_date = validate_and_process_date(due_date)

        # --- ORCHESTRATION LOGIC ---
        if intent == "create_task" and summary:
            # Create new task
            if outlook_access_token:
                try:
                    # Use LLM-extracted due date or fallback to current date
                    due_datetime = format_due_date_for_outlook(processed_due_date)
                    due_date_display = processed_due_date if processed_due_date else "Today (Malaysia time)"
                    
                    task_data = outlook_api.create_outlook_task(outlook_access_token, summary, due_datetime)
                    
                    # Store the created task for potential due date updates
                    store_user_last_task(user_id, task_data['id'], summary, processed_due_date)
                    
                    reply_message = f"✅ Task created in Outlook: '{summary}'\n📅 Due: {due_date_display}"
                    logger.info(f"Successfully created task in Outlook: '{summary}' with due date {due_date_display} (Malaysia timezone)")
                except Exception as outlook_error:
                    reply_message = f"❌ Failed to create task in Outlook: {outlook_error}"
                    logger.error(f"Error creating Outlook task: {outlook_error}")
            else:
                reply_message = "🔗 I need to connect to your Outlook first! Please use the /connectoutlook command."
                
        elif intent == "update_due_date" and processed_due_date:
            # Update existing task's due date
            last_task = get_user_last_task(user_id)
            if not last_task:
                reply_message = "❌ No recent task found to update. Create a task first, then I can help you change its due date."
            elif not outlook_access_token:
                reply_message = "🔗 I need to connect to your Outlook first! Please use the /connectoutlook command."
            else:
                try:
                    # Update the existing task's due date
                    due_datetime = format_due_date_for_outlook(processed_due_date)
                    
                    updated_task = outlook_api.update_task_due_date(outlook_access_token, last_task['id'], due_datetime)
                    
                    # Update our stored task info
                    store_user_last_task(user_id, last_task['id'], last_task['title'], processed_due_date)
                    
                    reply_message = f"✅ Updated task: '{last_task['title']}'\n📅 New due date: {processed_due_date}"
                    logger.info(f"Successfully updated task due date for user {user_id}: '{last_task['title']}' -> {processed_due_date}")
                except Exception as outlook_error:
                    reply_message = f"❌ Failed to update task due date: {outlook_error}"
                    logger.error(f"Error updating task due date: {outlook_error}")
                    
        else:
            # Handle other cases
            if intent == "unknown":
                reply_message = "🤔 I didn't detect a task creation or due date update request. Try phrases like:\n• 'remind me to...' (new task)\n• 'change due date to Friday' (update)"
            elif intent == "update_due_date" and not processed_due_date:
                reply_message = "❌ I couldn't extract a valid date from your message. Try formats like 'tomorrow', 'next Friday', or 'December 1st'."
            elif intent == "create_task" and not summary:
                reply_message = "❌ I need more details about the task you want to create."
            else:
                reply_message = f"📝 Analysis:\nIntent: {intent}\nSummary: {summary if summary else '[No summary]'}\nDue Date: {processed_due_date or 'None'}"
        
        # Truncate if message is too long for Telegram
        telegram_message_limit = 4096
        if len(reply_message) > telegram_message_limit:
            reply_message = reply_message[:telegram_message_limit - 50] + "\n\n... (message truncated)"
            logger.warning("Reply message was too long and has been truncated.")

        await update.message.reply_text(reply_message)
        logger.info(f"Replied with analysis: '{reply_message}'")

    except Exception as e:
        # Catch any other errors during processing
        await update.message.reply_text(
            "Oops! Something went wrong while processing your message. Please try again later."
        )
        logger.error(f"Error in echo handler: {e}")
