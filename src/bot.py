import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai
import os
import json
import outlook_api
from datetime import datetime, timezone
import pytz
import atexit
import signal
import sys

# Import refactored modules
from config.settings import config, constants
from utils.lock_manager import BotLockManager
from validators.task_validator import TaskValidator, ValidationResult

# Configure timezone for Malaysia (UTC+8) from config
MALAYSIA_TZ = config.timezone

# Initialize the Gemini model using config
genai.configure(api_key=config.gemini_api_key)
gemini_model = genai.GenerativeModel(config.gemini_model_name)

# Logging is already configured by config module
logger = logging.getLogger(__name__)

# Initialize validator with config settings
task_validator = TaskValidator(
    min_words=config.min_task_words,
    max_words=config.max_task_words
)

outlook_access_token = None

# Store last created task per user for due date updates
user_last_tasks = {}  # Dictionary to store {user_id: {"id": task_id, "title": task_title, "due_date": due_date}}

def store_user_last_task(user_id, task_id, task_title, due_date=None):
    """Store the user's last created task for potential updates"""
    user_last_tasks[user_id] = {
        "id": task_id,
        "title": task_title, 
        "due_date": due_date,
        "created_at": datetime.now(MALAYSIA_TZ)
    }
    logger.info(f"Stored last task for user {user_id}: {task_title}")

def get_user_last_task(user_id):
    """Get the user's last created task"""
    return user_last_tasks.get(user_id, None)

def validate_task_summary(summary, min_words=3, max_words=12):
    """
    Validate that a task summary meets word count requirements.
    
    Args:
        summary (str): The task summary to validate
        min_words (int): Minimum word count (default: 3)
        max_words (int): Maximum word count (default: 12)
    
    Returns:
        dict: {
            'is_valid': bool,
            'word_count': int,
            'message': str,
            'validated_summary': str
        }
    """
    if not summary or not isinstance(summary, str):
        return {
            'is_valid': False,
            'word_count': 0,
            'message': 'Summary is empty or not a string',
            'validated_summary': ''
        }
    
    # Clean and tokenize the summary
    cleaned_summary = ' '.join(summary.strip().split())  # Remove extra whitespace
    words = cleaned_summary.split()
    word_count = len(words)
    
    if word_count < min_words:
        return {
            'is_valid': False,
            'word_count': word_count,
            'message': f'Summary too short: {word_count} words (minimum: {min_words})',
            'validated_summary': cleaned_summary
        }
    elif word_count > max_words:
        return {
            'is_valid': False,
            'word_count': word_count,
            'message': f'Summary too long: {word_count} words (maximum: {max_words})',
            'validated_summary': cleaned_summary
        }
    else:
        return {
            'is_valid': True,
            'word_count': word_count,
            'message': f'Valid summary: {word_count} words',
            'validated_summary': cleaned_summary
        }

def generate_fallback_summary(user_message, max_attempts=2):
    """
    Generate a fallback summary from user message if LLM summary is invalid.
    
    Args:
        user_message (str): Original user message
        max_attempts (int): Maximum attempts to create valid summary
        
    Returns:
        str: A valid task summary within word limits
    """
    # Attempt 1: Extract key words from user message
    stop_words = {'i', 'me', 'to', 'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'for', 'with', 'from'}
    
    # Remove common task prefixes and clean message
    message_lower = user_message.lower()
    prefixes_to_remove = ['remind me to', 'i need to', 'i have to', 'i should', 'please remind me to', 'task:', 'todo:']
    
    cleaned_message = user_message
    for prefix in prefixes_to_remove:
        if message_lower.startswith(prefix):
            cleaned_message = user_message[len(prefix):].strip()
            break
    
    # Extract meaningful words
    words = cleaned_message.split()
    meaningful_words = []
    
    for word in words:
        clean_word = word.strip('.,!?;:').lower()
        if clean_word not in stop_words and len(clean_word) > 2:
            meaningful_words.append(word.strip('.,!?;:'))
    
    # Create summary within word limits
    if len(meaningful_words) >= 3:
        if len(meaningful_words) <= 12:
            return ' '.join(meaningful_words)
        else:
            # Truncate to 12 words
            return ' '.join(meaningful_words[:12])
    else:
        # Fallback: Use first 6 words of cleaned message
        fallback_words = cleaned_message.split()[:6]
        if len(fallback_words) >= 3:
            return ' '.join(fallback_words)
        else:
            # Ultimate fallback
            return f"Task from message: {user_message.split()[0] if user_message.split() else 'unknown'}"

def test_summary_validation():
    """Test function to verify summary validation works correctly"""
    test_cases = [
        ("Buy groceries", False),  # 2 words - too short
        ("Buy groceries and milk", True),  # 4 words - valid
        ("Call mom about dinner plans tonight", True),  # 6 words - valid  
        ("This is a very long task summary that exceeds the maximum word limit", False),  # Too long
        ("", False),  # Empty
        ("Complete important business meeting preparation tasks efficiently", True),  # 8 words - valid
    ]
    
    logger.info("Testing summary validation:")
    for test_summary, expected_valid in test_cases:
        result = validate_task_summary(test_summary)
        status = "✅ PASS" if result['is_valid'] == expected_valid else "❌ FAIL"
        logger.info(f"{status} - '{test_summary}' -> {result['word_count']} words, Valid: {result['is_valid']}")

# Utility function for date validation
def validate_and_process_date(date_string):
    """
    Validate and process a date string in YYYY-MM-DD format.
    Returns the processed date string or None if invalid.
    Uses Malaysia timezone for current date comparison.
    """
    if not date_string or date_string == "null":
        return None
    
    try:
        # Validate ISO date format (YYYY-MM-DD)
        parsed_date = datetime.fromisoformat(date_string).date()
        current_date_malaysia = datetime.now(MALAYSIA_TZ).date()
        
        # Check if date is not in the past (based on Malaysia timezone)
        if parsed_date >= current_date_malaysia:
            logger.info(f"Valid due date: {date_string}")
            return date_string
        else:
            logger.warning(f"Due date {date_string} is in the past (Malaysia time), using current date instead")
            return current_date_malaysia.isoformat()
    except (ValueError, TypeError) as date_error:
        logger.error(f"Invalid due date format '{date_string}': {date_error}")
        return None

def format_due_date_for_outlook(date_string):
    """
    Convert a YYYY-MM-DD date string to datetime format for Outlook API.
    Returns datetime in the format expected by Microsoft Graph API.
    Defaults to 5:00 PM Malaysia time on the specified date.
    """
    if not date_string:
        # Fallback to current date in Malaysia timezone
        malaysia_now = datetime.now(MALAYSIA_TZ).replace(hour=17, minute=0, second=0, microsecond=0)
        # Microsoft Graph expects datetime without timezone info (timezone specified separately)
        return malaysia_now.strftime("%Y-%m-%dT%H:%M:%S.0000000")
    
    try:
        # Parse the date and set time to 5:00 PM Malaysia time
        date_obj = datetime.fromisoformat(date_string).replace(hour=17, minute=0, second=0, microsecond=0)
        # Localize to Malaysia timezone 
        malaysia_datetime = MALAYSIA_TZ.localize(date_obj)
        # Microsoft Graph expects datetime in local timezone format without timezone suffix
        return malaysia_datetime.strftime("%Y-%m-%dT%H:%M:%S.0000000")
    except (ValueError, TypeError):
        # Fallback to current date/time in Malaysia timezone if parsing fails
        malaysia_now = datetime.now(MALAYSIA_TZ).replace(hour=17, minute=0, second=0, microsecond=0)
        return malaysia_now.strftime("%Y-%m-%dT%H:%M:%S.0000000")

def format_task_for_display(task, index):
    """
    Format a single task for Telegram display with proper markdown and emojis.
    
    Args:
        task (dict): Task object from Microsoft Graph API
        index (int): Task number for display (1-based)
    
    Returns:
        str: Formatted task string with emojis and markdown
    """
    try:
        # Get task title
        title = task.get('title', 'Untitled Task')
        
        # Format due date if available
        due_date_str = ""
        if task.get('dueDateTime') and task['dueDateTime'].get('dateTime'):
            try:
                # Parse the due date from ISO format
                due_datetime_utc = datetime.fromisoformat(task['dueDateTime']['dateTime'].replace('Z', '+00:00'))
                # Convert to Malaysia timezone
                due_datetime_malaysia = due_datetime_utc.astimezone(MALAYSIA_TZ)
                
                # Check if it's today, tomorrow, or overdue
                today = datetime.now(MALAYSIA_TZ).date()
                due_date = due_datetime_malaysia.date()
                
                if due_date < today:
                    due_date_str = f" - 🔴 **Overdue** ({due_datetime_malaysia.strftime('%b %d')})"
                elif due_date == today:
                    due_date_str = f" - 📅 **Due Today**"
                elif (due_date - today).days == 1:
                    due_date_str = f" - 📅 **Due Tomorrow**"
                else:
                    due_date_str = f" - 📅 Due {due_datetime_malaysia.strftime('%b %d')}"
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing due date for task '{title}': {e}")
                due_date_str = ""
        
        # Format importance/priority
        priority_str = ""
        if task.get('importance') == 'high':
            priority_str = " ⚡ **High Priority**"
        elif task.get('importance') == 'normal':
            # Don't show normal priority to avoid clutter
            pass
        elif task.get('importance') == 'low':
            priority_str = " 🔽 Low Priority"
        
        # Format the complete task line
        formatted_task = f"{index}. **{title}**{due_date_str}{priority_str}"
        
        return formatted_task
        
    except Exception as e:
        logger.error(f"Error formatting task for display: {e}")
        return f"{index}. {task.get('title', 'Untitled Task')}"

def format_tasks_list(tasks):
    """
    Format a list of tasks for Telegram display.
    
    Args:
        tasks (list): List of task objects from Microsoft Graph API
    
    Returns:
        str: Formatted task list with header and individual tasks
    """
    if not tasks:
        return "📋 **Your Tasks**\n\n🎉 **Congratulations!** You have no pending tasks! Time to relax or add some new goals! 🌟"
    
    task_count = len(tasks)
    header = f"📋 **Your Current Tasks** ({task_count} remaining)\n\n"
    
    # Format each task
    formatted_tasks = []
    for i, task in enumerate(tasks, 1):
        formatted_task = format_task_for_display(task, i)
        formatted_tasks.append(formatted_task)
    
    # Join all tasks
    tasks_text = "\n".join(formatted_tasks)
    
    return header + tasks_text

def get_motivational_message(task_count, overdue_count=0):
    """
    Generate a motivational message based on task count and status.
    
    Args:
        task_count (int): Total number of uncompleted tasks
        overdue_count (int): Number of overdue tasks (optional)
    
    Returns:
        str: Motivational message with emojis
    """
    import random
    
    if task_count == 0:
        celebration_messages = [
            "🎉 **Amazing!** You've completed all your tasks! Time to celebrate! 🌟",
            "🏆 **Inbox Zero achieved!** You're absolutely crushing it! 💪",
            "✨ **Perfect!** No pending tasks - you're on fire! 🔥",
            "🎯 **Goal accomplished!** All tasks done - take a well-deserved break! 🏖️",
            "🌟 **Outstanding!** Your task list is clear - keep up the excellent work! 🚀"
        ]
        return random.choice(celebration_messages)
    
    elif task_count <= 3:
        low_count_messages = [
            f"💪 **Almost there!** Just {task_count} tasks to go - you've got this! 🚀",
            f"🌟 **So close!** Only {task_count} tasks left - finish strong! 💥",
            f"🎯 **Nearly done!** {task_count} tasks remaining - you're doing great! ⭐",
            f"🔥 **On fire!** Just {task_count} more tasks and you're all set! 🏆",
            f"⚡ **Power through!** Only {task_count} tasks left - victory is near! 🌈"
        ]
        message = random.choice(low_count_messages)
    
    elif task_count <= 7:
        medium_count_messages = [
            f"💪 **You're doing great!** {task_count} tasks to tackle - one step at a time! 🌟",
            f"🚀 **Keep going!** {task_count} tasks remaining - you're making progress! 📈",
            f"⭐ **Stay strong!** {task_count} tasks on your list - you can handle this! 💫",
            f"🎯 **Focus time!** {task_count} tasks to complete - break them down and conquer! ⚡",
            f"🌟 **You've got this!** {task_count} tasks ahead - tackle them with confidence! 💪"
        ]
        message = random.choice(medium_count_messages)
    
    else:  # task_count > 7
        high_count_messages = [
            f"🎯 **Big list, bigger determination!** {task_count} tasks - start with the most important! 💪",
            f"🚀 **Challenge accepted!** {task_count} tasks to organize - you're capable of amazing things! ⭐",
            f"💫 **Take it step by step!** {task_count} tasks - prioritize and make progress! 🌟",
            f"⚡ **You're a productivity hero!** {task_count} tasks - break them into smaller wins! 🏆",
            f"🌈 **Every journey starts with one step!** {task_count} tasks - pick one and begin! 🔥"
        ]
        message = random.choice(high_count_messages)
    
    # Add overdue task warning if applicable
    if overdue_count > 0:
        overdue_warning = f"\n🔴 **Heads up:** {overdue_count} task{'s' if overdue_count > 1 else ''} overdue - consider tackling {'them' if overdue_count > 1 else 'it'} first!"
        message += overdue_warning
    
    return message

# 3. Define handler functions for different types of messages

# This function is called when the user sends the /start command
async def start(update: Update, _context):
    """Sends a welcoming message when the command /start is issued."""
    user = update.effective_user
    welcome_message = f"""Hi {user.mention_html()}! 🤖

I'm your personal task management assistant! Here's what I can do:

📝 **Create Tasks**: Send me any message describing a task, and I'll create it in your Outlook Tasks
📅 **Set Due Dates**: Include dates like "tomorrow", "next Friday", or "2024-12-25" in your message
📋 **View Tasks**: Use /mytasks to see your current uncompleted tasks with motivational messages
🔗 **Connect Outlook**: Use /connectoutlook to link your Microsoft account

🇲🇾 All dates and times are handled in Malaysia timezone (UTC+8).

Try sending me a task or use /mytasks to get started!"""
    
    await update.message.reply_html(welcome_message)
    logger.info(f"User {user.first_name} ({user.id}) started the bot.")

# This function is called when the user sends any text message
# Ensure GEMINI_API_KEY and gemini_model are defined above this function as in the previous guide

async def echo(update: Update, context):
    """
    Sends the user's message to Gemini, extracts intent and summary,
    and replies with the structured response.
    """
    user_message = update.message.text
    logger.info(f"Received message from {update.effective_user.first_name}: '{user_message}'")

    if not config.gemini_api_key:
        await update.message.reply_text("Error: Gemini API Key not configured. Please set GEMINI_API_KEY environment variable.")
        logger.error("Gemini API Key is missing.")
        return

    try:
        # --- START OF NEW PROMPT & LLM CALL LOGIC ---
        # 1. Craft a precise prompt with enhanced date detection (using Malaysia timezone)
        current_date = datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d")
        current_weekday = datetime.now(MALAYSIA_TZ).strftime("%A")
        
        # Check if user has a recent task for update context
        user_id = update.effective_user.id
        last_task = get_user_last_task(user_id)
        last_task_context = ""
        if last_task:
            last_task_context = f"User's last created task: '{last_task['title']}' (due: {last_task.get('due_date', 'no date set')}). "
        
        prompt_parts = [
            "You are an intelligent task assistant. Your job is to analyze user requests and identify if they want to:",
            "1. Create a new task",
            "2. Update the due date of their last created task", 
            "3. Something else (unknown intent)",
            f"Context: Today is {current_date} ({current_weekday}) in Malaysia timezone (UTC+8). {last_task_context}",
            "Always respond with a JSON object with three keys: 'intent', 'summary', and 'due_date'.",
            "Intent Detection Rules:",
            "- Set 'intent' to 'create_task' if the user wants to create/add/remember a NEW task",
            "- Set 'intent' to 'update_due_date' if the user wants to change/update/modify the due date of their existing task",
            "- Set 'intent' to 'unknown' for other requests",
            "Summary Rules:",
            "- For new tasks: provide a concise task summary using EXACTLY 3-12 words (no more, no less)",
            "- Focus on action verbs and key nouns, avoid articles and filler words",
            "- Examples: 'Buy groceries' (2 words - too short), 'Buy groceries and milk' (4 words - good), 'Call mom about dinner plans' (5 words - good)",
            "- For due date updates: use empty string (the existing task title will be used)",
            "- For unknown: use empty string",
            "Due Date Extraction Rules:",
            "- Extract explicit dates: 'October 26th' -> '2025-10-26', 'Dec 15' -> '2025-12-15'",
            "- Handle relative dates: 'tomorrow' -> next day, 'next Friday' -> next occurring Friday", 
            "- Process time expressions: 'in 3 days' -> 3 days from today, 'next week' -> 7 days from today",
            "- Handle ambiguous dates: 'Friday' (if today is Wednesday) -> this Friday, 'Monday' (if today is Wednesday) -> next Monday",
            "- Set 'due_date' to YYYY-MM-DD format or null if no date found",
            "- If user says 'today', use today's date. If 'tonight' or 'this evening', also use today's date",
            "- All dates should be calculated based on Malaysia timezone",
            "Examples:",
            "User: 'Buy groceries tomorrow' -> {'intent': 'create_task', 'summary': 'Buy groceries and supplies', 'due_date': '2025-09-24'}",
            "User: 'Change due date to Friday' -> {'intent': 'update_due_date', 'summary': '', 'due_date': '2025-09-27'}",
            "User: 'Update due date to next week' -> {'intent': 'update_due_date', 'summary': '', 'due_date': '2025-10-01'}",
            "User: 'Move deadline to December 1st' -> {'intent': 'update_due_date', 'summary': '', 'due_date': '2025-12-01'}",
            "User: 'Set due date tomorrow' -> {'intent': 'update_due_date', 'summary': '', 'due_date': '2025-09-25'}",
            "User: 'Submit report by December 1st' -> {'intent': 'create_task', 'summary': 'Submit important quarterly report', 'due_date': '2025-12-01'}",
            "User: 'What time is it?' -> {'intent': 'unknown', 'summary': '', 'due_date': null}",
            f"Now analyze this request and provide your JSON response:\nUser Request: '{user_message}'"
        ]

        # Send the carefully crafted prompt to Gemini
        response = gemini_model.generate_content(prompt_parts)
        llm_raw_text_reply = response.text
        # --- END OF NEW PROMPT & LLM CALL LOGIC ---

        def extract_json_from_response(response_text):
            """Extract JSON from Gemini response, handling various markdown formats"""
            response_text = response_text.strip()
            
            # Handle ```json ... ``` format
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    return response_text[start:end].strip()
            
            # Handle ``` ... ``` format
            elif response_text.startswith("```") and response_text.count("```") >= 2:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    return response_text[start:end].strip()
            
            # Handle plain JSON (no markdown)
            elif response_text.startswith("{") and response_text.endswith("}"):
                return response_text
            
            # Try to find JSON object in the text
            else:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    return response_text[start:end]
            
            return response_text

        llm_json_string = extract_json_from_response(llm_raw_text_reply)

        # 2. Parse the LLM's response to extract structured data
        try:
            # Assuming Gemini returns a valid JSON string
            parsed_response = json.loads(llm_json_string)
            
            # Extract intent, summary, and due_date
            intent = parsed_response.get("intent", "unknown") # Use .get() for safety
            raw_summary = parsed_response.get("summary", "")    # Use .get() for safety
            due_date = parsed_response.get("due_date", None)  # Extract due_date
            
            logger.info(f"LLM Response - Intent: {intent}, Raw Summary: '{raw_summary}', Due Date: {due_date}")
            
            # Validate task summary word count (only for create_task intent)
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
            
            summary = validated_summary  # Use the validated summary
            
            # Validate and process the due_date using utility function
            processed_due_date = validate_and_process_date(due_date)

            # --- START OF ORCHESTRATION LOGIC ---
            if intent == "create_task" and summary: # Only proceed if intent is 'create_task' AND we have a summary
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
                    
            elif intent == "update_due_date" and processed_due_date: # Handle due date updates
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
            # --- END OF ORCHESTRATION LOGIC ---

        except json.JSONDecodeError:
            logger.error(f"Gemini did not return valid JSON: {llm_raw_text_reply}")
            reply_message = "Gemini had trouble understanding that. Could you rephrase?"
        
        # Truncation logic (from previous step, still good to keep)
        telegram_message_limit = 4096
        if len(reply_message) > telegram_message_limit:
            reply_message = reply_message[:telegram_message_limit - 50] + "\n\n... (message truncated)"
            logger.warning("Gemini analysis message was too long and has been truncated.")

        await update.message.reply_text(reply_message)
        logger.info(f"Replied with Gemini's analysis: '{reply_message}'")

    except Exception as e:
        # Catch any other errors during the Gemini API call or other unexpected issues
        await update.message.reply_text(
            "Oops! Something went wrong while talking to Gemini. Please try again later."
        )
        logger.error(f"Error calling Gemini API: {e}")

# This function handles errors
async def error(update: Update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

# --- New Handler for Outlook Connection ---
async def connect_outlook(update: Update, context):
    """Initiates the Outlook device code flow for authentication."""
    global outlook_access_token
    await update.message.reply_text("Initiating Outlook connection...")
    try:
        # Call the get_auth_token from our outlook_api module
        # Change this line:
        # token, auth_message_for_user = outlook_api.get_auth_token()
        
        # To this:
        token = outlook_api.get_auth_token()
        outlook_access_token = token # Store the token globally
        await update.message.reply_text(
            "✅ Outlook connected successfully! You can now create tasks by sending me task descriptions.\n🇲🇾 All times will be handled in Malaysia timezone (UTC+8)."
        )
        logger.info("Successfully connected to Outlook")
    except Exception as e:
        await update.message.reply_text(f"Failed to connect to Outlook: {e}")
        logger.error(f"Error in connect_outlook: {e}")

# Rate limiting dictionary to track last /mytasks usage per user
user_last_mytasks_request = {}

async def my_tasks(update: Update, context):
    """
    Handle /mytasks command to display user's uncompleted Outlook tasks with motivational messages.
    Implements rate limiting to prevent API abuse (max 1 request per minute per user).
    """
    global outlook_access_token
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"User {user_name} ({user_id}) requested /mytasks")
    
    # Check if user is authenticated
    if not outlook_access_token:
        await update.message.reply_text(
            "🔗 **Please connect to Outlook first!**\n"
            "Use the /connectoutlook command to authenticate your account."
        )
        logger.warning(f"User {user_id} tried to use /mytasks without authentication")
        return
    
    # Rate limiting: Check if user has made a request in the last minute
    current_time = datetime.now(MALAYSIA_TZ)
    if user_id in user_last_mytasks_request:
        time_since_last_request = current_time - user_last_mytasks_request[user_id]
        if time_since_last_request.total_seconds() < 60:  # 60 seconds = 1 minute
            remaining_seconds = 60 - int(time_since_last_request.total_seconds())
            await update.message.reply_text(
                f"⏱️ **Please wait {remaining_seconds} seconds** before requesting tasks again.\n"
                "This helps prevent overwhelming the server! 😊"
            )
            logger.info(f"Rate limited user {user_id}, {remaining_seconds} seconds remaining")
            return
    
    # Update last request time
    user_last_mytasks_request[user_id] = current_time
    
    try:
        # Show "typing" indicator while fetching tasks
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Fetch uncompleted tasks from Outlook
        logger.info(f"Fetching uncompleted tasks for user {user_id}")
        uncompleted_tasks = outlook_api.get_uncompleted_tasks(outlook_access_token, max_tasks=10)
        
        # Count overdue tasks
        overdue_count = 0
        today = datetime.now(MALAYSIA_TZ).date()
        
        for task in uncompleted_tasks:
            if task.get('dueDateTime') and task['dueDateTime'].get('dateTime'):
                try:
                    due_datetime_utc = datetime.fromisoformat(task['dueDateTime']['dateTime'].replace('Z', '+00:00'))
                    due_date = due_datetime_utc.astimezone(MALAYSIA_TZ).date()
                    if due_date < today:
                        overdue_count += 1
                except (ValueError, TypeError):
                    continue
        
        # Format tasks for display
        tasks_display = format_tasks_list(uncompleted_tasks)
        
        # Get motivational message
        motivational_message = get_motivational_message(len(uncompleted_tasks), overdue_count)
        
        # Combine tasks display and motivational message
        full_message = f"{tasks_display}\n\n{motivational_message}"
        
        # Send the formatted message
        await update.message.reply_text(full_message, parse_mode='Markdown')
        logger.info(f"Successfully sent {len(uncompleted_tasks)} tasks to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in my_tasks command for user {user_id}: {e}")
        await update.message.reply_text(
            "❌ **Oops! Something went wrong** while fetching your tasks.\n"
            "This might be a temporary issue. Please try again in a moment, or check your Outlook connection with /connectoutlook."
        )

# 4. Main function to set up and run the bot
def main():
    """Start the bot."""
    try:
        # Create the Application and pass it your bot's token from config
        application = Application.builder().token(config.telegram_bot_token).build()

        # Register handlers
        # CommandHandler is for commands like /start
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("connectoutlook", connect_outlook)) # Add this line
        application.add_handler(CommandHandler("mytasks", my_tasks)) # Add new /mytasks command

        # MessageHandler is for regular messages.
        # filters.TEXT means it processes only text messages.
        # ~filters.COMMAND means it ignores messages that are commands (like /start).
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        # Register error handler
        application.add_error_handler(error)

        # Validation test moved to validators/task_validator.py
        # Can run: task_validator.test_validation() if needed

        logger.info("Starting bot...")
        
        # Start the Bot with conflict handling
        # polling() listens for updates from Telegram's servers.
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot started and is polling for updates...")
        
    except Exception as e:
        if "409" in str(e) or "Conflict" in str(e):
            logger.error("❌ Bot conflict detected! Another instance may be running.")
            logger.error("Please make sure no other bot instances are active and try again.")
            logger.error("You can check for running Python processes and terminate them if needed.")
        else:
            logger.error(f"❌ Failed to start bot: {e}")
        raise

# Note: Lock file mechanism has been moved to utils/lock_manager.py

if __name__ == '__main__':
    # Initialize lock manager using config
    lock_manager = BotLockManager(config.lock_file_path)
    
    # Acquire lock to prevent multiple instances
    if not lock_manager.acquire_lock():
        logger.error("Another bot instance is running. Exiting.")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        lock_manager.release_lock()