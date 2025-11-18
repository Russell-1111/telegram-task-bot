# Architecture Examples

**Practical usage patterns for the Phase 1-3 refactored architecture**

This document provides real-world examples of how to use the service layer, handlers, and utilities in the Telegram Task Bot. Each example includes error handling, best practices, and integration patterns.

---

## Table of Contents

1. [Service Layer Examples](#service-layer-examples)
   - [OutlookService](#outlookservice)
   - [StateManager](#statemanager)
   - [TokenManager](#tokenmanager)
   - [LLMService](#llmservice)
2. [Integration Patterns](#integration-patterns)
   - [Authentication Flow](#authentication-flow)
   - [Task Creation Flow](#task-creation-flow)
   - [Message Handling Flow](#message-handling-flow)
3. [Handler Examples](#handler-examples)
   - [Command Handlers](#command-handlers)
   - [Message Handlers](#message-handlers)
4. [Testing Examples](#testing-examples)
   - [Unit Testing](#unit-testing)
   - [Mocking Patterns](#mocking-patterns)
   - [Integration Testing](#integration-testing)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Common Recipes](#common-recipes)

---

## Service Layer Examples

### OutlookService

The `OutlookService` provides a clean abstraction over the Microsoft Graph API for Outlook Tasks.

#### Example 1: Basic Task Creation

```python
from src.services.outlook_service import OutlookService

# Initialize the service
outlook_service = OutlookService()

# Create a simple task
try:
    task = outlook_service.create_task(
        access_token="your_access_token",
        task_title="Complete project documentation",
        due_date_iso="2025-10-10"
    )
    print(f"Task created with ID: {task['id']}")
except Exception as e:
    print(f"Failed to create task: {e}")
```

#### Example 2: Task Creation with Full Error Handling

```python
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager

def create_task_safely(user_id: int, title: str, due_date: str):
    """Create a task with comprehensive error handling."""
    outlook_service = OutlookService()
    token_manager = TokenManager()
    
    # Check if user has a valid token
    if not token_manager.has_token(user_id):
        return {
            "success": False,
            "error": "User not authenticated. Please use /login first."
        }
    
    # Get the access token
    access_token = token_manager.get_token(user_id)
    
    # Attempt to create the task
    try:
        task = outlook_service.create_task(
            access_token=access_token,
            task_title=title,
            due_date_iso=due_date
        )
        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created successfully!"
        }
    except ValueError as e:
        # Invalid date format
        return {
            "success": False,
            "error": f"Invalid date format: {e}"
        }
    except Exception as e:
        # API or network error
        return {
            "success": False,
            "error": f"Failed to create task: {e}"
        }
```

#### Example 3: Retrieving and Filtering Tasks

```python
from src.services.outlook_service import OutlookService
from datetime import datetime, timedelta

def get_upcoming_tasks(access_token: str, days: int = 7):
    """Get tasks due in the next N days."""
    outlook_service = OutlookService()
    
    try:
        # Get all uncompleted tasks
        all_tasks = outlook_service.get_uncompleted_tasks(access_token)
        
        # Filter for upcoming tasks
        cutoff_date = datetime.now() + timedelta(days=days)
        upcoming_tasks = []
        
        for task in all_tasks:
            if task.get('dueDateTime'):
                due_date = datetime.fromisoformat(
                    task['dueDateTime']['dateTime'].replace('Z', '+00:00')
                )
                if due_date <= cutoff_date:
                    upcoming_tasks.append(task)
        
        return {
            "success": True,
            "tasks": upcoming_tasks,
            "count": len(upcoming_tasks)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

#### Example 4: Batch Task Operations

```python
from src.services.outlook_service import OutlookService

def delete_old_tasks(access_token: str, days_old: int = 30):
    """Delete tasks older than N days."""
    outlook_service = OutlookService()
    
    try:
        # Get all uncompleted tasks
        tasks = outlook_service.get_uncompleted_tasks(access_token)
        
        # Filter old tasks
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        errors = []
        
        for task in tasks:
            if task.get('createdDateTime'):
                created_date = datetime.fromisoformat(
                    task['createdDateTime'].replace('Z', '+00:00')
                )
                if created_date < cutoff_date:
                    try:
                        outlook_service.delete_task(access_token, task['id'])
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"Failed to delete {task['title']}: {e}")
        
        return {
            "success": True,
            "deleted": deleted_count,
            "errors": errors
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

### StateManager

The `StateManager` centralizes user state management, replacing the old global dictionary pattern.

#### Example 1: Basic State Management

```python
from src.utils.state_manager import UserStateManager

# Initialize the manager
state_manager = UserStateManager()

# Set user state
state_manager.set_user_task(
    user_id=123456,
    task_id="outlook_task_123",
    task_title="Buy groceries",
    due_date="2025-10-05"
)

# Check if user has pending state
if state_manager.has_user_task(123456):
    task_data = state_manager.get_user_task(123456)
    print(f"User has pending task: {task_data['title']}")

# Clear state when done
state_manager.clear_user_task(123456)
```

#### Example 2: State-Based Conversation Flow

```python
from src.utils.state_manager import UserStateManager
from telegram import Update
from telegram.ext import ContextTypes

state_manager = UserStateManager()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages with state awareness."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user has pending task creation
    if state_manager.has_user_task(user_id):
        task_data = state_manager.get_user_task(user_id)
        
        # User is providing additional details
        # Note: Custom metadata should be stored in task_data dict
        if task_data.get("waiting_for") == "due_date":
            # User is providing the due date
            # Update by setting new task with updated info
            state_manager.set_user_task(
                user_id=user_id,
                task_id=task_data.get('task_id', 'temp'),
                task_title=task_data['title'],
                due_date=text  # User's new input
            )
            
            await update.message.reply_text(
                f"Task: {task_data['title']}\n"
                f"Due: {text}\n\n"
                "Reply 'confirm' to create or 'cancel' to abort."
            )
        elif task_data.get("waiting_for") == "confirmation":
            if text.lower() == "confirm":
                # Create the task
                # ... task creation logic ...
                state_manager.clear_user_task(user_id)
                await update.message.reply_text("Task created!")
            else:
                state_manager.clear_user_task(user_id)
                await update.message.reply_text("Task creation cancelled.")
    else:
        # Normal message handling
        await update.message.reply_text("How can I help you?")
```

#### Example 3: Complex State Management

```python
from src.utils.state_manager import UserStateManager
from datetime import datetime

def manage_multi_step_task_creation(user_id: int, step: str, data: dict):
    """Manage a multi-step task creation process."""
    state_manager = UserStateManager()
    
    # Get current state or initialize
    if state_manager.has_user_task(user_id):
        task_data = state_manager.get_user_task(user_id)
    else:
        task_data = {
            "step": "title",
            "started_at": datetime.now().isoformat(),
            "title": "",
            "due_date": None,
            "task_id": "temp"
        }
    
    # Update based on current step
    if step == "title":
        task_data["title"] = data["title"]
        task_data["step"] = "due_date"
        state_manager.set_user_task(
            user_id=user_id,
            task_id=task_data["task_id"],
            task_title=task_data["title"],
            due_date=task_data.get("due_date")
        )
    elif step == "due_date":
        task_data["due_date"] = data["due_date"]
        task_data["step"] = "priority"
        state_manager.set_user_task(
            user_id=user_id,
            task_id=task_data["task_id"],
            task_title=task_data["title"],
            due_date=task_data["due_date"]
        )
    elif step == "priority":
        # Note: Priority is not stored in StateManager
        # Would need to be handled separately or in a custom field
        task_data["step"] = "complete"
    
    return task_data
```

---

### TokenManager

The `TokenManager` handles access token lifecycle management, replacing the global token variable.

**Note**: TokenManager is a global single-user token store, not per-user. For multi-user bots, you'd need a different approach.

#### Example 1: Basic Token Management

```python
from src.utils.token_manager import TokenManager

# Initialize the manager
token_manager = TokenManager()

# Store a token (global for the bot, not per-user)
token_manager.set_token("eyJ0eXAiOiJKV1QiLCJub25jZSI6...")

# Check if there's a valid token
if token_manager.has_token():
    token = token_manager.get_token()
    print(f"Token available: {token[:20]}...")
else:
    print("No token found - user needs to authenticate")
```

#### Example 2: Token Expiration Handling

```python
from src.utils.token_manager import TokenManager
from datetime import timedelta

def check_token_validity() -> dict:
    """Check if the token is valid and not expired."""
    token_manager = TokenManager()
    
    if not token_manager.has_token():
        return {
            "valid": False,
            "reason": "No token found. Please authenticate with /connectoutlook."
        }
    
    # Get token age
    token_age = token_manager.get_token_age()
    
    if token_age is None:
        return {
            "valid": False,
            "reason": "Token age unknown"
        }
    
    # Tokens typically expire after 1 hour
    if token_age > 3600:  # 3600 seconds = 1 hour
        return {
            "valid": False,
            "reason": "Token expired. Please re-authenticate with /connectoutlook.",
            "age_seconds": token_age
        }
    
    # Token is valid
    return {
        "valid": True,
        "token": token_manager.get_token(),
        "age_seconds": token_age
    }
```

#### Example 3: Token Information Display

```python
from src.utils.token_manager import TokenManager

async def show_token_status() -> str:
    """Generate a user-friendly token status message."""
    token_manager = TokenManager()
    
    if not token_manager.has_token():
        return "❌ Not authenticated. Use /connectoutlook to authenticate."
    
    token_info = token_manager.get_token_info()
    token_age = token_manager.get_token_age()
    
    if token_age is None:
        return "⚠️ Token status unknown."
    
    # Calculate time remaining (assuming 1 hour expiry)
    time_remaining_seconds = 3600 - token_age
    
    if time_remaining_seconds <= 0:
        return "⚠️ Token expired. Please use /connectoutlook to re-authenticate."
    
    minutes_remaining = int(time_remaining_seconds / 60)
    
    return (
        f"✅ Authenticated\n"
        f"Token Age: {int(token_age)} seconds\n"
        f"Time Remaining: ~{minutes_remaining} minutes"
    )
```

---

### LLMService

The `LLMService` provides AI-powered task parsing and natural language understanding.

#### Example 1: Basic Task Parsing

```python
from src.services.llm_service import LLMService
from datetime import datetime
import pytz

# Initialize the service
from src.config.settings import config
llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)

# Parse a natural language task
user_message = "Remind me to call mom tomorrow at 3pm"

try:
    # Get current date for context
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_date = datetime.now(malaysia_tz)
    
    # Analyze the task request
    task_intent = llm_service.analyze_task_request(
        user_message=user_message,
        current_date=current_date,
        last_task_context=None
    )
    
    print(f"Intent: {task_intent.intent}")
    print(f"Summary: {task_intent.summary}")
    print(f"Due Date: {task_intent.due_date}")
except Exception as e:
    print(f"Failed to parse task: {e}")
```

#### Example 2: Task Parsing with Validation

```python
from src.services.llm_service import LLMService
from src.validators.task_validator import TaskValidator
from src.formatters.date_formatter import validate_and_process_date
from datetime import datetime
import pytz

def parse_and_validate_task(user_message: str):
    """Parse user message and validate the resulting task."""
    from src.config.settings import config
    llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
    validator = TaskValidator()
    
    try:
        # Get current date for LLM context
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_date = datetime.now(malaysia_tz)
        
        # Parse the task using LLM
        task_intent = llm_service.analyze_task_request(
            user_message=user_message,
            current_date=current_date,
            last_task_context=None
        )
        
        # Validate summary
        summary_validation = validator.validate_summary(task_intent.summary)
        if not summary_validation.is_valid:
            return {
                "success": False,
                "error": f"Invalid summary: {summary_validation.message}"
            }
        
        # Validate date (if provided)
        if task_intent.due_date:
            validated_date = validate_and_process_date(task_intent.due_date)
            if not validated_date:
                return {
                    "success": False,
                    "error": "Invalid date format"
                }
        
        return {
            "success": True,
            "task": {
                "intent": task_intent.intent,
                "summary": task_intent.summary,
                "due_date": task_intent.due_date
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to parse task: {e}"
        }
```

#### Example 3: Context-Aware Parsing

```python
from src.services.llm_service import LLMService
from src.utils.state_manager import UserStateManager
from datetime import datetime
import pytz

def parse_with_context(user_id: int, message: str):
    """Parse task with user context from previous interactions."""
    from src.config.settings import config
    llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
    state_manager = UserStateManager()
    
    # Get current date
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_date = datetime.now(malaysia_tz)
    
    # Build context from previous interactions
    last_task_context = None
    if state_manager.has_user_task(user_id):
        previous_task = state_manager.get_user_task(user_id)
        last_task_context = {
            'title': previous_task.get('title', 'N/A'),
            'due_date': previous_task.get('due_date')
        }
    
    try:
        task_intent = llm_service.analyze_task_request(
            user_message=message,
            current_date=current_date,
            last_task_context=last_task_context
        )
        return {
            "success": True,
            "task": {
                "intent": task_intent.intent,
                "summary": task_intent.summary,
                "due_date": task_intent.due_date
            },
            "context_used": bool(last_task_context)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## Integration Patterns

### Authentication Flow

Complete authentication workflow showing service integration.

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.utils.token_manager import TokenManager
from src.config.settings import Settings
import msal

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /connectoutlook command - complete authentication flow."""
    token_manager = TokenManager()
    from src.config.settings import config
    import msal
    
    # Check if already authenticated
    if token_manager.has_token():
        token_age = token_manager.get_token_age()
        await update.message.reply_text(
            f"✅ Already authenticated!\n"
            f"Token age: {int(token_age)} seconds\n\n"
            f"Use /logout to sign out."
        )
        return
    
    # Build MSAL authentication URL
    app = msal.PublicClientApplication(
        config.ms_client_id,
        authority=f"https://login.microsoftonline.com/{config.ms_tenant_id}"
    )
    
    flow = app.initiate_device_flow(scopes=["Tasks.ReadWrite"])
    
    if "user_code" not in flow:
        await update.message.reply_text("❌ Failed to initiate login flow.")
        return
    
    # Display authentication instructions
    keyboard = [[
        InlineKeyboardButton(
            "🔐 Authenticate",
            url=flow["verification_uri"]
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔐 **Microsoft Authentication**\n\n"
        f"1. Click the button below\n"
        f"2. Enter code: `{flow['user_code']}`\n"
        f"3. Sign in with your Microsoft account\n\n"
        f"Waiting for authentication...",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Poll for authentication
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        # Store the token (global, not per-user)
        token_manager.set_token(result["access_token"])
        
        await update.message.reply_text(
            "✅ **Authentication Successful!**\n\n"
            "You can now create and manage tasks."
        )
    else:
        await update.message.reply_text(
            f"❌ Authentication failed: {result.get('error_description', 'Unknown error')}"
        )
```

---

### Task Creation Flow

Complete task creation workflow with validation and error handling.

```python
from telegram import Update
from telegram.ext import ContextTypes
from src.services.llm_service import LLMService
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager
from src.utils.state_manager import UserStateManager
from src.validators.task_validator import TaskValidator
from datetime import datetime
import pytz

async def handle_task_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete task creation flow from user message."""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Initialize services
    from src.config.settings import config
    llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
    outlook_service = OutlookService()
    token_manager = TokenManager()
    state_manager = UserStateManager()
    validator = TaskValidator()
    
    # Step 1: Check authentication
    if not token_manager.has_token():
        await update.message.reply_text(
            "❌ Please authenticate first using /connectoutlook"
        )
        return
    
    # Step 2: Parse the task using LLM
    try:
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        current_date = datetime.now(malaysia_tz)
        
        # Get last task context
        last_task_context = None
        if state_manager.has_user_task(user_id):
            last_task = state_manager.get_user_task(user_id)
            last_task_context = {
                'title': last_task['title'],
                'due_date': last_task.get('due_date')
            }
        
        task_intent = llm_service.analyze_task_request(
            user_message=message_text,
            current_date=current_date,
            last_task_context=last_task_context
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Couldn't understand your request: {e}\n\n"
            "Try: 'Create task: Buy milk, due tomorrow'"
        )
        return
    
    # Step 3: Validate the parsed task
    summary_validation = validator.validate_summary(task_intent.summary)
    if not summary_validation.is_valid:
        await update.message.reply_text(
            f"❌ Invalid task summary: {summary_validation.message}"
        )
        return
    
    # Step 4: Show preview (simplified - actual implementation would store for confirmation)
    preview_message = (
        f"📋 **Task Preview**\n\n"
        f"Title: {task_intent.summary}\n"
        f"Due: {task_intent.due_date or 'No due date'}\n\n"
        "Reply 'yes' to create or 'no' to cancel."
    )
    
    await update.message.reply_text(preview_message)
    
    # Note: Actual confirmation handling would be in a separate handler

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task creation confirmation."""
    user_id = update.effective_user.id
    confirmation = update.message.text.lower()
    
    # Initialize services
    outlook_service = OutlookService()
    token_manager = TokenManager()
    state_manager = UserStateManager()
    
    # Check if user has pending task
    if not state_manager.has_user_task(user_id):
        return  # Not in task creation flow
    
    task_data = state_manager.get_user_task(user_id)
    
    # Note: In real implementation, you'd check custom metadata for "waiting_for"
    # StateManager only stores task_id, title, due_date
    
    if confirmation in ["yes", "y", "confirm", "ok"]:
        # Step 6: Create the task in Outlook
        access_token = token_manager.get_token()
        
        try:
            created_task = outlook_service.create_task(
                access_token=access_token,
                task_title=task_data["title"],
                due_date_iso=task_data.get("due_date")
            )
            
            # Clear state
            state_manager.clear_user_task(user_id)
            
            await update.message.reply_text(
                f"✅ Task created successfully!\n\n"
                f"Title: {created_task.get('title', 'Unknown')}\n"
                f"ID: {created_task.get('id', 'N/A')[:8]}..."
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Failed to create task: {e}"
            )
    else:
        # Clear state
        state_manager.clear_user_task(user_id)
        
        await update.message.reply_text("Task creation cancelled.")
```

---

### Message Handling Flow

How message handlers coordinate multiple services.

```python
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from src.services.llm_service import LLMService
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager
from src.utils.state_manager import UserStateManager
from src.utils.token_manager import TokenManager
from src.services.llm_service import LLMService

async def intelligent_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages with intelligent routing based on context."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Initialize services
    from src.config.settings import config
    state_manager = UserStateManager()
    token_manager = TokenManager()
    llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
    
    # Route 1: User has pending state (multi-step flow)
    if state_manager.has_user_task(user_id):
        await handle_stateful_message(update, context)
        return
    
    # Route 2: User is not authenticated
    if not token_manager.has_token():
        await update.message.reply_text(
            "👋 Welcome! Please use /connectoutlook to authenticate first."
        )
        return
    
    # Route 3: Detect intent using LLM
    try:
        # Use LLM to classify the message
        intent = await classify_intent(text, llm_service)
        
        if intent == "create_task":
            await handle_task_message(update, context)
        elif intent == "list_tasks":
            await handle_list_tasks(update, context)
        elif intent == "help":
            await update.message.reply_text(
                "I can help you:\n"
                "• Create tasks\n"
                "• List your tasks\n"
                "• Update task dates\n\n"
                "Try: 'Show my tasks' or 'Create task: Buy milk'"
            )
        else:
            await update.message.reply_text(
                "I didn't understand. Try /help for available commands."
            )
    except Exception as e:
        await update.message.reply_text(
            f"Error processing message: {e}"
        )

async def classify_intent(text: str, llm_service: LLMService) -> str:
    """Use LLM to classify user intent."""
    # Simplified - in real implementation, use LLM API
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["create", "add", "new task", "remind"]):
        return "create_task"
    elif any(word in text_lower for word in ["list", "show", "my tasks", "tasks"]):
        return "list_tasks"
    elif any(word in text_lower for word in ["help", "what can", "how to"]):
        return "help"
    else:
        return "unknown"
```

---

## Handler Examples

### Command Handlers

Practical examples from `src/handlers/command_handlers.py`.

#### Example 1: Start Command with Service Integration

```python
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.token_manager import TokenManager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with authentication status check."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    token_manager = TokenManager()
    
    # Check authentication status
    is_authenticated = token_manager.has_token(user_id)
    
    welcome_message = f"👋 Hello {user_name}!\n\n"
    
    if is_authenticated:
        welcome_message += (
            "✅ You're already authenticated!\n\n"
            "**What you can do:**\n"
            "• Create tasks with natural language\n"
            "• List your tasks with /mytasks\n"
            "• Update task dates\n"
            "• Delete old tasks\n\n"
            "Try: 'Create task: Finish report by Friday'"
        )
    else:
        welcome_message += (
            "To get started:\n"
            "1. Use /login to authenticate\n"
            "2. Follow the authentication steps\n"
            "3. Start creating tasks!\n\n"
            "Need help? Use /help"
        )
    
    await update.message.reply_text(welcome_message)
```

#### Example 2: MyTasks Command with Formatting

```python
from telegram import Update
from telegram.ext import ContextTypes
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager
from src.formatters.task_formatter import TaskFormatter

async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mytasks command - list all uncompleted tasks."""
    user_id = update.effective_user.id
    token_manager = TokenManager()
    outlook_service = OutlookService()
    formatter = TaskFormatter()
    
    # Check authentication
    if not token_manager.has_token(user_id):
        await update.message.reply_text(
            "❌ Please authenticate first using /login"
        )
        return
    
    # Get access token
    access_token = token_manager.get_token(user_id)
    
    try:
        # Fetch tasks
        tasks = outlook_service.get_uncompleted_tasks(access_token)
        
        if not tasks:
            await update.message.reply_text("📋 You have no active tasks!")
            return
        
        # Format tasks
        formatted_tasks = formatter.format_task_list(tasks)
        
        response = f"📋 **Your Tasks** ({len(tasks)} total)\n\n{formatted_tasks}"
        
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to retrieve tasks: {e}\n\n"
            "Your token may have expired. Try /login again."
        )
```

---

### Message Handlers

Examples from `src/handlers/message_handlers.py`.

#### Example 1: Stateful Message Handling

```python
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.state_manager import UserStateManager
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages with state awareness."""
    user_id = update.effective_user.id
    text = update.message.text
    
    state_manager = UserStateManager()
    
    # Check for pending state
    if state_manager.has_user_task(user_id):
        task_data = state_manager.get_user_task(user_id)
        
        # Note: StateManager only stores task_id, title, due_date
        # For "waiting_for" state, you'd need custom metadata storage
        await handle_stateful_message(update, context, task_data)
    else:
        # New conversation - route based on content
        await route_new_message(update, context)

async def handle_due_date_input(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    task_data: dict
):
    """Handle user providing a due date."""
    from src.validators.task_validator import TaskValidator
    from src.formatters.date_formatter import validate_and_process_date
    
    user_id = update.effective_user.id
    date_text = update.message.text
    state_manager = UserStateManager()
    validator = TaskValidator()
    
    # Validate the date
    validated_date = validate_and_process_date(date_text)
    
    if not validated_date:
        await update.message.reply_text(
            f"❌ Invalid date format\n\n"
            "Please provide a valid date (e.g., '2025-10-10' or 'tomorrow')"
        )
        return
    
    # Update state with validated date
    state_manager.set_user_task(
        user_id=user_id,
        task_id=task_data.get('task_id', 'temp'),
        task_title=task_data['title'],
        due_date=validated_date
    )
    
    await update.message.reply_text(
        f"Task: {task_data['title']}\n"
        f"Due: {validated_date}\n\n"
        "Reply 'yes' to create or 'no' to cancel."
    )
```

---

## Testing Examples

### Unit Testing

Example unit tests for services and utilities.

#### Example 1: Testing OutlookService

```python
import unittest
from unittest.mock import Mock, patch
from src.services.outlook_service import OutlookService

class TestOutlookService(unittest.TestCase):
    def setUp(self):
        self.service = OutlookService()
        self.mock_token = "mock_access_token"
    
    @patch('src.services.outlook_service.outlook_api')
    def test_create_task_success(self, mock_outlook_api):
        """Test successful task creation."""
        # Arrange
        mock_outlook_api.create_task.return_value = {
            "id": "task123",
            "title": "Test Task",
            "status": "notStarted"
        }
        
        # Act
        result = self.service.create_task(
            access_token=self.mock_token,
            task_title="Test Task",
            due_date_iso="2025-10-10"
        )
        
        # Assert
        self.assertEqual(result["id"], "task123")
        self.assertEqual(result["title"], "Test Task")
        mock_outlook_api.create_task.assert_called_once()
    
    @patch('src.services.outlook_service.outlook_api')
    def test_create_task_api_error(self, mock_outlook_api):
        """Test task creation with API error."""
        # Arrange
        mock_outlook_api.create_task.side_effect = Exception("API Error")
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.service.create_task(
                access_token=self.mock_token,
                title="Test Task",
                due_date="2025-10-10"
            )
        
        self.assertIn("API Error", str(context.exception))
```

#### Example 2: Testing StateManager

```python
import unittest
from src.utils.state_manager import UserStateManager

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.manager = UserStateManager()
        self.user_id = 123456
    
    def test_set_and_get_task(self):
        """Test setting and retrieving task data."""
        # Arrange
        task_id = "outlook_task_123"
        title = "Test Task"
        due_date = "2025-10-10"
        
        # Act
        self.manager.set_user_task(
            user_id=self.user_id,
            task_id=task_id,
            task_title=title,
            due_date=due_date
        )
        result = self.manager.get_user_task(self.user_id)
        
        # Assert
        self.assertEqual(result["title"], "Test Task")
        self.assertEqual(result["due_date"], "2025-10-10")
        self.assertEqual(result["task_id"], "outlook_task_123")
    
    def test_has_user_task(self):
        """Test checking if user has task data."""
        # Act & Assert
        self.assertFalse(self.manager.has_user_task(self.user_id))
        
        self.manager.set_user_task(
            user_id=self.user_id,
            task_id="task123",
            task_title="Test",
            due_date=None
        )
        self.assertTrue(self.manager.has_user_task(self.user_id))
    
    def test_clear_user_task(self):
        """Test clearing user task data."""
        # Arrange
        self.manager.set_user_task(
            user_id=self.user_id,
            task_id="task123",
            task_title="Test",
            due_date=None
        )
        
        # Act
        self.manager.clear_user_task(self.user_id)
        
        # Assert
        self.assertFalse(self.manager.has_user_task(self.user_id))
        self.assertIsNone(self.manager.get_user_task(self.user_id))
```

---

### Mocking Patterns

Advanced mocking patterns for testing handlers.

#### Example 1: Mocking Telegram Update

```python
import unittest
from unittest.mock import AsyncMock, Mock, patch
from telegram import Update, Message, User, Chat
from src.handlers.command_handlers import start_command

class TestCommandHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Create mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 123456
        self.mock_user.first_name = "TestUser"
        
        # Create mock chat
        self.mock_chat = Mock(spec=Chat)
        self.mock_chat.id = 123456
        
        # Create mock message
        self.mock_message = Mock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        self.mock_message.chat = self.mock_chat
        
        # Create mock update
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Create mock context
        self.mock_context = Mock()
    
    @patch('src.handlers.command_handlers.TokenManager')
    async def test_start_command_authenticated(self, mock_token_manager_class):
        """Test /start command for authenticated user."""
        # Arrange
        mock_token_manager = Mock()
        mock_token_manager.has_token.return_value = True
        mock_token_manager_class.return_value = mock_token_manager
        
        # Act
        await start_command(self.mock_update, self.mock_context)
        
        # Assert
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("already authenticated", call_args.lower())
```

#### Example 2: Mocking Service Layer

```python
import unittest
from unittest.mock import Mock, patch, AsyncMock
from src.handlers.message_handlers import handle_task_message

class TestMessageHandlers(unittest.IsolatedAsyncioTestCase):
    @patch('src.handlers.message_handlers.OutlookService')
    @patch('src.handlers.message_handlers.LLMService')
    @patch('src.handlers.message_handlers.TokenManager')
    @patch('src.handlers.message_handlers.StateManager')
    async def test_task_creation_flow(
        self,
        mock_state_manager_class,
        mock_token_manager_class,
        mock_llm_service_class,
        mock_outlook_service_class
    ):
        """Test complete task creation flow."""
        # Arrange
        mock_update = Mock()
        mock_update.effective_user.id = 123456
        mock_update.message.text = "Create task: Buy milk tomorrow"
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = Mock()
        
        # Mock TokenManager
        mock_token_manager = Mock()
        mock_token_manager.has_token.return_value = True
        mock_token_manager_class.return_value = mock_token_manager
        
        # Mock LLMService
        mock_llm_service = Mock()
        mock_llm_service.parse_task.return_value = {
            "title": "Buy milk",
            "due_date": "2025-10-04"
        }
        mock_llm_service_class.return_value = mock_llm_service
        
        # Act
        await handle_task_message(mock_update, mock_context)
        
        # Assert
        mock_llm_service.parse_task.assert_called_once()
        mock_update.message.reply_text.assert_called()
```

---

### Integration Testing

Testing service integration with real dependencies.

```python
import unittest
import os
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager
from src.config.settings import Settings

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.settings = Settings()
        
        # Skip if no test credentials
        if not cls.settings.AZURE_CLIENT_ID:
            raise unittest.SkipTest("No Azure credentials configured")
    
    def test_full_task_lifecycle(self):
        """Test creating, updating, and deleting a task."""
        outlook_service = OutlookService()
        token_manager = TokenManager()
        
        # This requires a valid test token
        test_user_id = 999999
        test_token = os.getenv("TEST_ACCESS_TOKEN")
        
        if not test_token:
            self.skipTest("No test access token available")
        
        token_manager.set_token(test_user_id, test_token)
        
        # Create task
        created_task = outlook_service.create_task(
            access_token=test_token,
            task_title="Integration Test Task",
            due_date_iso="2025-12-31"
        )
        
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task["title"], "Integration Test Task")
        
        task_id = created_task["id"]
        
        # Update task
        updated_task = outlook_service.update_task_due_date(
            access_token=test_token,
            task_id=task_id,
            new_due_date="2026-01-15"
        )
        
        self.assertIsNotNone(updated_task)
        
        # Delete task
        outlook_service.delete_task(test_token, task_id)
        
        # Verify deletion
        tasks = outlook_service.get_uncompleted_tasks(test_token)
        task_ids = [t["id"] for t in tasks]
        self.assertNotIn(task_id, task_ids)
```

---

## Error Handling Patterns

### Pattern 1: Graceful Degradation

```python
from src.services.outlook_service import OutlookService
from src.utils.token_manager import TokenManager

async def create_task_with_fallback(user_id: int, title: str, due_date: str):
    """Create task with graceful degradation on errors."""
    outlook_service = OutlookService()
    token_manager = TokenManager()
    
    # Level 1: Check authentication
    if not token_manager.has_token(user_id):
        return {
            "success": False,
            "error": "not_authenticated",
            "message": "Please authenticate with /login first",
            "user_action": "Use /login command"
        }
    
    access_token = token_manager.get_token(user_id)
    
    # Level 2: Attempt creation
    try:
        task = outlook_service.create_task(access_token, title, due_date)
        return {
            "success": True,
            "task": task,
            "message": f"Task '{title}' created successfully!"
        }
    except ValueError as e:
        # Level 3: Invalid input - ask user to correct
        return {
            "success": False,
            "error": "invalid_input",
            "message": f"Invalid input: {e}",
            "user_action": "Please check your date format"
        }
    except Exception as e:
        # Level 4: Unknown error - provide debug info
        if "401" in str(e) or "unauthorized" in str(e).lower():
            return {
                "success": False,
                "error": "token_expired",
                "message": "Your session has expired",
                "user_action": "Please use /login to re-authenticate"
            }
        else:
            return {
                "success": False,
                "error": "unknown",
                "message": f"Unexpected error: {e}",
                "user_action": "Please try again or contact support"
            }
```

### Pattern 2: Retry Logic

```python
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise
            
            # Calculate backoff time
            wait_time = backoff_factor ** attempt
            
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)

# Usage example
async def create_task_with_retry(access_token: str, title: str, due_date: str):
    """Create task with automatic retry on failure."""
    outlook_service = OutlookService()
    
    return await retry_with_backoff(
        outlook_service.create_task,
        max_retries=3,
        access_token=access_token,
        title=title,
        due_date=due_date
    )
```

---

## Common Recipes

### Recipe 1: Task Batch Import

```python
from src.services.outlook_service import OutlookService
import csv

def import_tasks_from_csv(access_token: str, csv_file_path: str):
    """Import multiple tasks from a CSV file."""
    outlook_service = OutlookService()
    results = {
        "success": [],
        "failed": []
    }
    
    with open(csv_file_path, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            title = row.get('title')
            due_date = row.get('due_date')
            
            if not title or not due_date:
                results["failed"].append({
                    "row": row,
                    "error": "Missing title or due_date"
                })
                continue
            
            try:
                task = outlook_service.create_task(
                    access_token=access_token,
                    task_title=title,
                    due_date_iso=due_date
                )
                results["success"].append(task)
            except Exception as e:
                results["failed"].append({
                    "row": row,
                    "error": str(e)
                })
    
    return results
```

### Recipe 2: Smart Task Reminders

```python
from src.services.outlook_service import OutlookService
from datetime import datetime, timedelta
from telegram import Bot

async def send_task_reminders(bot: Bot, user_id: int, access_token: str):
    """Send reminders for tasks due soon."""
    outlook_service = OutlookService()
    
    # Get all tasks
    tasks = outlook_service.get_uncompleted_tasks(access_token)
    
    # Filter tasks due in next 24 hours
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    urgent_tasks = []
    for task in tasks:
        if task.get('dueDateTime'):
            due_date = datetime.fromisoformat(
                task['dueDateTime']['dateTime'].replace('Z', '+00:00')
            )
            if now <= due_date <= tomorrow:
                urgent_tasks.append(task)
    
    if urgent_tasks:
        message = f"⏰ **Reminder: {len(urgent_tasks)} task(s) due soon!**\n\n"
        for task in urgent_tasks:
            message += f"• {task['title']}\n"
        
        await bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
```

### Recipe 3: Task Statistics

```python
from src.services.outlook_service import OutlookService
from datetime import datetime
from collections import Counter

def get_task_statistics(access_token: str) -> dict:
    """Generate statistics about user's tasks."""
    outlook_service = OutlookService()
    
    tasks = outlook_service.get_uncompleted_tasks(access_token)
    
    # Count by status
    status_counts = Counter(task.get('status', 'unknown') for task in tasks)
    
    # Count overdue tasks
    now = datetime.now()
    overdue_count = 0
    
    for task in tasks:
        if task.get('dueDateTime'):
            due_date = datetime.fromisoformat(
                task['dueDateTime']['dateTime'].replace('Z', '+00:00')
            )
            if due_date < now:
                overdue_count += 1
    
    # Calculate average tasks per day (last 7 days)
    week_ago = now - timedelta(days=7)
    recent_tasks = [
        task for task in tasks
        if task.get('createdDateTime') and
        datetime.fromisoformat(task['createdDateTime'].replace('Z', '+00:00')) >= week_ago
    ]
    
    return {
        "total_tasks": len(tasks),
        "overdue": overdue_count,
        "status_breakdown": dict(status_counts),
        "recent_tasks_7d": len(recent_tasks),
        "avg_per_day": len(recent_tasks) / 7
    }
```

---

## Summary

This examples document demonstrates:

1. **Service Layer**: Complete examples for OutlookService, StateManager, TokenManager, and LLMService
2. **Integration Patterns**: Real-world workflows showing how services work together
3. **Handler Examples**: Command and message handlers with proper error handling
4. **Testing**: Unit tests, mocking patterns, and integration tests
5. **Error Handling**: Graceful degradation and retry logic
6. **Common Recipes**: Practical solutions for batch operations, reminders, and statistics

**Key Principles Demonstrated:**
- ✅ Clean separation of concerns
- ✅ Comprehensive error handling
- ✅ State management best practices
- ✅ Testable code patterns
- ✅ User-friendly error messages
- ✅ Service layer abstraction

**Next Steps:**
- Refer to [API.md](API.md) for detailed API reference
- See [TESTING-GUIDE.md](../TESTING-GUIDE.md) for testing instructions
- Check [README.md](../README.md) for project overview

---

*Last Updated: October 3, 2025*
*Architecture Version: Phase 3 Complete*
