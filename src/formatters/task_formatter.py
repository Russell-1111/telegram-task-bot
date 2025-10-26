"""
Task formatting module for Telegram display.

This module handles:
- Formatting individual tasks with emojis and markdown
- Formatting task lists with headers and counts
- Generating motivational messages based on task status
"""

import logging
import random
from datetime import datetime
import pytz
import re

logger = logging.getLogger(__name__)

# Malaysia timezone for consistent date handling
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def escape_markdown(text):
    """
    Escape special characters for Telegram Markdown.
    
    In Telegram Markdown, certain characters need to be escaped with a backslash
    to prevent parsing errors. This function handles: _ * [ ] ( ) ~ ` > # + - = | { } . !
    
    Args:
        text (str): Text to escape
    
    Returns:
        str: Escaped text safe for Telegram Markdown
    
    Example:
        >>> escape_markdown("Task_with_underscores")
        'Task\\_with\\_underscores'
    """
    if not text:
        return text
    
    # Characters that need escaping in Telegram Markdown
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each special character
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    return text


def format_task_for_display(task, index):
    """
    Format a single task for Telegram display with proper markdown and emojis.
    
    Features:
    - Displays task number and title
    - Shows due date with context (today, tomorrow, overdue, upcoming)
    - Indicates priority with emojis (high priority, low priority)
    - Uses Telegram markdown for emphasis
    - Converts dates to Malaysia timezone
    
    Args:
        task (dict): Task object from Microsoft Graph API with keys:
                    - title: Task title
                    - dueDateTime: Due date object with 'dateTime' key
                    - importance: Priority level ('high', 'normal', 'low')
        index (int): Task number for display (1-based)
    
    Returns:
        str: Formatted task string with emojis and markdown
             Format: "1. **Task Title** - 📅 Due Tomorrow ⚡ **High Priority**"
    
    Example:
        >>> task = {
        ...     'title': 'Complete project proposal',
        ...     'dueDateTime': {'dateTime': '2024-12-31T17:00:00.0000000'},
        ...     'importance': 'high'
        ... }
        >>> format_task_for_display(task, 1)
        '1. **Complete project proposal** - 📅 Due Dec 31 ⚡ **High Priority**'
    """
    try:
        # Get task title and escape special characters
        title = task.get('title', 'Untitled Task')
        # Escape markdown special characters to prevent parsing errors
        escaped_title = escape_markdown(title)
        
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
        formatted_task = f"{index}. **{escaped_title}**{due_date_str}{priority_str}"
        
        return formatted_task
        
    except Exception as e:
        logger.error(f"Error formatting task for display: {e}")
        # Return safely escaped version on error
        safe_title = escape_markdown(task.get('title', 'Untitled Task'))
        return f"{index}. {safe_title}"


def format_tasks_list(tasks):
    """
    Format a list of tasks for Telegram display.
    
    Features:
    - Shows task count in header
    - Displays each task with formatting
    - Provides congratulatory message when no tasks exist
    - Uses consistent markdown formatting
    
    Args:
        tasks (list): List of task objects from Microsoft Graph API
                     Each task should have keys: title, dueDateTime, importance
    
    Returns:
        str: Formatted task list with header and individual tasks
             Includes task count and motivational header
    
    Example:
        >>> tasks = [
        ...     {'title': 'Buy groceries', 'importance': 'normal'},
        ...     {'title': 'Finish report', 'importance': 'high'}
        ... ]
        >>> print(format_tasks_list(tasks))
        📋 **Your Current Tasks** (2 remaining)
        
        1. **Buy groceries**
        2. **Finish report** ⚡ **High Priority**
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
    
    Features:
    - Randomized messages to keep interactions fresh
    - Different tones based on task count (0, 1-3, 4-7, 8+)
    - Celebration messages for empty task lists
    - Warnings for overdue tasks
    - Emoji-rich for engaging user experience
    
    Args:
        task_count (int): Total number of uncompleted tasks
        overdue_count (int): Number of overdue tasks (optional, default: 0)
    
    Returns:
        str: Motivational message with emojis and markdown
             Includes overdue warning if applicable
    
    Example:
        >>> msg = get_motivational_message(5, 2)
        >>> "tasks" in msg.lower()
        True
        >>> "overdue" in msg.lower()
        True
    """
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
