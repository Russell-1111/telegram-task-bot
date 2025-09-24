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

# Configure timezone for Malaysia (UTC+8)
# All date/time operations in this bot use Malaysia timezone
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# Configure Gemini API (REPLACE WITH YOUR ACTUAL API KEY)
# It's best practice to load API keys from environment variables or a config file
# For now, we'll put it directly, but remember to replace this for real projects!
# For a quick start, you can paste your key directly:
# GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
# Even better, load from environment variable (see tip below):
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model
# We're using 'gemini-1.5-flash-latest' for its speed and cost-effectiveness
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# 1. Set up logging (optional, but good practice for debugging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Define your bot's API Token (REPLACE WITH YOUR ACTUAL TOKEN!)
TELEGRAM_BOT_TOKEN = "8487024063:AAEEuIPLgwMBHJpzn99b_0YDR4BaSxKHv9I"

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

# 3. Define handler functions for different types of messages

# This function is called when the user sends the /start command
async def start(update: Update, _context):
    """Sends a welcoming message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Send me any text, and I'll echo it back."
    )
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

    if not GEMINI_API_KEY:
        await update.message.reply_text("Error: Gemini API Key not configured. Please set GEMINI_API_KEY.")
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
                validation_result = validate_task_summary(raw_summary)
                
                if validation_result['is_valid']:
                    validated_summary = validation_result['validated_summary']
                    logger.info(f"Valid task summary: '{validated_summary}' ({validation_result['word_count']} words)")
                else:
                    logger.warning(f"Invalid task summary: {validation_result['message']}")
                    # Attempt to generate a fallback summary
                    validated_summary = generate_fallback_summary(user_message)
                    fallback_validation = validate_task_summary(validated_summary)
                    
                    if fallback_validation['is_valid']:
                        logger.info(f"Generated valid fallback summary: '{validated_summary}' ({fallback_validation['word_count']} words)")
                    else:
                        logger.error(f"Fallback summary also invalid: {fallback_validation['message']}")
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

# 4. Main function to set up and run the bot
def main():
    """Start the bot."""
    try:
        # Create the Application and pass it your bot's token.
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        # CommandHandler is for commands like /start
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("connectoutlook", connect_outlook)) # Add this line

        # MessageHandler is for regular messages.
        # filters.TEXT means it processes only text messages.
        # ~filters.COMMAND means it ignores messages that are commands (like /start).
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

        # Register error handler
        application.add_error_handler(error)

        # Run validation test on startup (optional - can be removed in production)
        if logger.isEnabledFor(logging.INFO):
            test_summary_validation()

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

# Lock file mechanism to prevent multiple instances
LOCK_FILE = "bot.lock"

def create_lock_file():
    """Create a lock file to prevent multiple instances"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if the process is still running (Windows)
            import subprocess
            try:
                result = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, text=True)
                # Check if the process actually exists in the output
                if f"python" in result.lower() and str(pid) in result:
                    logger.error(f"❌ Bot is already running with PID {pid}")
                    logger.error("Please stop the existing instance first or delete the bot.lock file if no bot is running.")
                    sys.exit(1)
                else:
                    # Process not running, remove stale lock file and continue
                    os.remove(LOCK_FILE)
                    logger.info(f"Removed stale lock file (PID {pid} no longer running)")
            except subprocess.CalledProcessError:
                # Process not running, remove stale lock file and continue
                os.remove(LOCK_FILE)
                logger.info(f"Removed stale lock file (PID {pid} no longer running)")
        except (ValueError, FileNotFoundError):
            # Invalid lock file, remove it
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
    
    # Create new lock file
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"Created lock file with PID {os.getpid()}")

def remove_lock_file():
    """Remove the lock file on exit"""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
        logger.info("Removed lock file")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    remove_lock_file()
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Register cleanup function
    atexit.register(remove_lock_file)
    
    # Check for existing instances
    create_lock_file()
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        remove_lock_file()