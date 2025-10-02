"""
Command handlers for Telegram bot commands.

This module handles:
- /start command: Welcome message and bot introduction
- /connectoutlook command: Outlook authentication flow
- /mytasks command: Display user's uncompleted tasks with rate limiting
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

import outlook_api
from formatters import format_tasks_list, get_motivational_message

logger = logging.getLogger(__name__)

# Malaysia timezone for consistent date handling
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# Global variable to store Outlook access token (shared with message_handlers)
# In a production app, this should be managed differently (per-user storage, database, etc.)
outlook_access_token = None

# Rate limiting dictionary to track last /mytasks usage per user
user_last_mytasks_request = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command with welcome message.
    
    Features:
    - Personalized greeting with user's name
    - Overview of bot capabilities
    - Instructions for getting started
    - Links to important commands
    - Timezone information (Malaysia)
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context object
    
    Returns:
        None (sends message via Telegram API)
    
    Example:
        User: /start
        Bot: Hi @username! 🤖
             I'm your personal task management assistant! Here's what I can do:
             📝 **Create Tasks**: Send me any message describing a task...
    """
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


async def connect_outlook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiate the Outlook device code flow for authentication.
    
    Features:
    - Initiates Microsoft device code flow
    - Stores access token globally (TODO: per-user storage)
    - Provides user feedback throughout process
    - Comprehensive error handling and logging
    
    Process:
    1. Notify user that connection is starting
    2. Call outlook_api.get_auth_token() to start device code flow
    3. User completes authentication in browser
    4. Store access token for subsequent API calls
    5. Confirm successful connection
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context object
    
    Returns:
        None (sends messages via Telegram API)
    
    Technical Note:
        Currently stores token in global variable. In production:
        - Use per-user storage (database, cache)
        - Implement token refresh logic
        - Handle token expiration gracefully
    
    Example:
        User: /connectoutlook
        Bot: Initiating Outlook connection...
             [User completes auth in browser]
             ✅ Outlook connected successfully! You can now create tasks...
    """
    global outlook_access_token
    await update.message.reply_text("Initiating Outlook connection...")
    try:
        # Call the get_auth_token from our outlook_api module
        # This starts the device code flow and returns the access token
        token = outlook_api.get_auth_token()
        outlook_access_token = token  # Store the token globally
        await update.message.reply_text(
            "✅ Outlook connected successfully! You can now create tasks by sending me task descriptions.\n"
            "🇲🇾 All times will be handled in Malaysia timezone (UTC+8)."
        )
        logger.info("Successfully connected to Outlook")
    except Exception as e:
        await update.message.reply_text(f"Failed to connect to Outlook: {e}")
        logger.error(f"Error in connect_outlook: {e}")


async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /mytasks command to display user's uncompleted Outlook tasks.
    
    Features:
    - Fetches uncompleted tasks from Outlook API
    - Displays tasks with formatting (due dates, priorities)
    - Counts overdue tasks
    - Generates motivational messages
    - Implements rate limiting (1 request/minute per user)
    - Shows typing indicator while fetching
    - Comprehensive error handling
    
    Rate Limiting:
    - Maximum 1 request per minute per user
    - Prevents API abuse and server overload
    - Provides helpful countdown message when rate limited
    - Tracked in user_last_mytasks_request dictionary
    
    Args:
        update (Update): Telegram update object
        context (ContextTypes.DEFAULT_TYPE): Telegram context object
    
    Returns:
        None (sends messages via Telegram API)
    
    Technical Details:
        - Uses Malaysia timezone for date calculations
        - Fetches max 10 tasks from API
        - Parses due dates to identify overdue tasks
        - Formats output using formatters module
        - Handles authentication errors gracefully
    
    Example:
        User: /mytasks
        Bot: 📋 **Your Current Tasks** (3 remaining)
             
             1. **Buy groceries** - 📅 Due Today
             2. **Submit report** - 🔴 **Overdue** (Dec 10) ⚡ **High Priority**
             3. **Call dentist** - 📅 Due Tomorrow
             
             💪 **Almost there!** Just 3 tasks to go - you've got this! 🚀
             🔴 **Heads up:** 1 task overdue - consider tackling it first!
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


# Module-level function to set the outlook token (for use by message_handlers)
def set_outlook_token(token):
    """Set the global outlook access token."""
    global outlook_access_token
    outlook_access_token = token


# Module-level function to get the outlook token (for use by message_handlers)
def get_outlook_token():
    """Get the global outlook access token."""
    return outlook_access_token
