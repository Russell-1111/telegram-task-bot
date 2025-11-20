"""
Message handlers for Telegram bot regular messages.

This module handles:
- echo() function: Processes user messages for task creation/updates
- LLM integration for intent detection
- Task creation in Outlook
- Due date updates for existing tasks
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
import pytz

# Import from sibling modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import config
from services import LLMService, OutlookService
from validators import TaskValidator
from formatters import validate_and_process_date, format_due_date_for_outlook

logger = logging.getLogger(__name__)

# Malaysia timezone for consistent date handling
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# Initialize services and utilities
llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
task_validator = TaskValidator()
outlook_service = OutlookService()

# Global references to managers (set by bot.py via command_handlers)
state_manager = None
token_manager = None

def set_managers(token_mgr, state_mgr):
    """
    Set the manager instances from bot.py.
    
    Note: Handlers must extract user_id from update.effective_user.id
    and pass it to token_manager methods.
    
    Args:
        token_mgr: TokenManager instance
        state_mgr: UserStateManager instance
    """
    global token_manager, state_manager
    token_manager = token_mgr
    state_manager = state_mgr


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process user messages for task creation and due date updates.
    
    Features:
    - LLM-powered intent detection (create_task, update_due_date, unknown)
    - Task summary validation (3-12 words)
    - Fallback summary generation for invalid LLM outputs
    - Date parsing and validation (Malaysia timezone)
    - Outlook task creation with due dates via OutlookService
    - Due date updates for existing tasks
    - Comprehensive error handling and user feedback
    
    Workflow:
    1. Receive user message
    2. Send to LLM service for intent analysis
    3. Validate task summary (if creating task)
    4. Process due date (if provided)
    5. Call OutlookService (create or update)
    6. Store task info in StateManager for future updates
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
        Uses TokenManager for token storage and StateManager for user state.
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Received message from {update.effective_user.first_name}: '{user_message}'")

    if not config.gemini_api_key:
        await update.message.reply_text("Error: Gemini API Key not configured. Please set GEMINI_API_KEY environment variable.")
        logger.error("Gemini API Key is missing.")
        return

    try:
        # STEP 1: Validate input relevance BEFORE sending to LLM
        relevance_check = task_validator.validate_input_relevance(user_message)
        logger.info(f"Relevance check - Task-related: {relevance_check.is_task_related}, "
                   f"Category: {relevance_check.detected_category}, "
                   f"Confidence: {relevance_check.confidence:.2f}")
        
        if not relevance_check.is_task_related:
            # Input is not task-related - provide helpful feedback
            category_responses = {
                "greeting": "👋 Hello! I'm a task management bot. To create a task, tell me what you need to do.\n\n"
                           "Examples:\n• 'Buy groceries tomorrow'\n• 'Call dentist on Friday'\n• 'Submit report by Dec 15'",
                
                "question": "🤔 I'm a task management bot, not a Q&A assistant. I can help you create and manage tasks in Outlook.\n\n"
                           "To create a task, describe what you need to do:\n• 'Prepare presentation for Monday'\n• 'Pay bills by end of week'",
                
                "irrelevant": "💬 I didn't detect a task in your message. I specialize in creating Outlook tasks.\n\n"
                             "Try telling me something you need to do:\n• 'Schedule meeting with team'\n• 'Review project documents tomorrow'",
                
                "unclear": "🤷 I'm not sure what you want me to do. I help create tasks in Outlook.\n\n"
                          "Please describe a specific task:\n• 'Book flight for next month'\n• 'Finish homework by Wednesday'"
            }
            
            response = category_responses.get(
                relevance_check.detected_category,
                "ℹ️ I'm a task management bot. Tell me what you need to do and I'll create an Outlook task.\n\n"
                "Examples:\n• 'Buy milk and eggs'\n• 'Complete project proposal tomorrow'"
            )
            
            await update.message.reply_text(response)
            logger.info(f"Rejected non-task input. Category: {relevance_check.detected_category}, Reason: {relevance_check.reason}")
            return
        
        # STEP 2: Input is task-related - proceed with LLM analysis
        # Get current date for LLM context
        current_date = datetime.now(MALAYSIA_TZ)
        
        # Get user's last task for update context from StateManager
        last_task = state_manager.get_user_task(user_id)
        last_task_context = None
        if last_task:
            last_task_context = {
                'title': last_task['title'],
                'due_date': last_task.get('due_date')
            }
        
        # Analyze user message with LLM service (async call)
        task_intent = await llm_service.analyze_task_request(
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
            if token_manager.has_token(user_id):
                try:
                    # Use LLM-extracted due date or fallback to current date
                    due_datetime = format_due_date_for_outlook(processed_due_date)
                    due_date_display = processed_due_date if processed_due_date else "Today (Malaysia time)"
                    
                    access_token = token_manager.get_token(user_id)
                    task_data = await outlook_service.create_task(access_token, summary, due_datetime)
                    
                    # Store the created task in StateManager for potential due date updates
                    state_manager.set_user_task(user_id, task_data['id'], summary, processed_due_date)
                    
                    reply_message = f"✅ Task created in Outlook: '{summary}'\n📅 Due: {due_date_display}"
                    logger.info(f"Successfully created task in Outlook for user {user_id}: '{summary}' with due date {due_date_display} (Malaysia timezone)")
                except Exception as outlook_error:
                    reply_message = f"❌ Failed to create task in Outlook: {outlook_error}"
                    logger.error(f"Error creating Outlook task for user {user_id}: {outlook_error}")
            else:
                reply_message = "🔗 I need to connect to your Outlook first! Please use the /connectoutlook command."
                
        elif intent == "update_due_date" and processed_due_date:
            # Update existing task's due date
            last_task = state_manager.get_user_task(user_id)
            if not last_task:
                reply_message = "❌ No recent task found to update. Create a task first, then I can help you change its due date."
            elif not token_manager.has_token(user_id):
                reply_message = "🔗 I need to connect to your Outlook first! Please use the /connectoutlook command."
            else:
                try:
                    # Update the existing task's due date
                    due_datetime = format_due_date_for_outlook(processed_due_date)
                    
                    access_token = token_manager.get_token(user_id)
                    updated_task = await outlook_service.update_task_due_date(access_token, last_task['id'], due_datetime)
                    
                    # Update our stored task info in StateManager
                    state_manager.set_user_task(user_id, last_task['id'], last_task['title'], processed_due_date)
                    
                    reply_message = f"✅ Updated task: '{last_task['title']}'\n📅 New due date: {processed_due_date}"
                    logger.info(f"Successfully updated task due date for user {user_id}: '{last_task['title']}' -> {processed_due_date}")
                except Exception as outlook_error:
                    reply_message = f"❌ Failed to update task due date: {outlook_error}"
                    logger.error(f"Error updating task due date for user {user_id}: {outlook_error}")
                    
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
