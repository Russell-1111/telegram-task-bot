"""
Pytest configuration and shared fixtures for all tests
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import pytz

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Timezone for testing
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram Update object"""
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456
    update.effective_user.first_name = "TestUser"
    update.effective_user.mention_html = Mock(return_value="@TestUser")
    
    update.message = Mock()
    update.message.text = "Test message"
    update.message.reply_text = AsyncMock()
    update.message.reply_html = AsyncMock()
    
    update.effective_chat = Mock()
    update.effective_chat.id = 123456
    
    return update


@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram Context object"""
    context = Mock()
    context.bot = Mock()
    context.bot.send_chat_action = AsyncMock()
    return context


@pytest.fixture
def sample_outlook_task():
    """Create a sample Outlook task for testing"""
    return {
        'id': 'AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5e-T-3V',
        'title': 'Test Task',
        'status': 'notStarted',
        'importance': 'normal',
        'createdDateTime': '2025-10-26T10:00:00.0000000',
        'dueDateTime': {
            'dateTime': '2025-10-28T17:00:00.0000000',
            'timeZone': 'Asia/Kuala_Lumpur'
        }
    }


@pytest.fixture
def sample_high_priority_task():
    """Create a sample high priority Outlook task"""
    return {
        'id': 'AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5e-T-3V',
        'title': 'Urgent Task',
        'status': 'notStarted',
        'importance': 'high',
        'createdDateTime': '2025-10-26T10:00:00.0000000',
        'dueDateTime': {
            'dateTime': '2025-10-27T17:00:00.0000000',
            'timeZone': 'Asia/Kuala_Lumpur'
        }
    }


@pytest.fixture
def sample_overdue_task():
    """Create a sample overdue Outlook task"""
    return {
        'id': 'AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5e-T-3V',
        'title': 'Overdue Task',
        'status': 'notStarted',
        'importance': 'high',
        'createdDateTime': '2025-10-20T10:00:00.0000000',
        'dueDateTime': {
            'dateTime': '2025-10-25T17:00:00.0000000',
            'timeZone': 'Asia/Kuala_Lumpur'
        }
    }


@pytest.fixture
def current_date_malaysia():
    """Get current date in Malaysia timezone"""
    return datetime.now(MALAYSIA_TZ)


@pytest.fixture
def mock_access_token():
    """Mock Microsoft Graph API access token"""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik5HVEZ2ZEstZnl0aEV1Q..."


@pytest.fixture
def sample_task_intent():
    """Create a sample TaskIntent for testing"""
    from services.llm_service import TaskIntent
    return TaskIntent(
        intent="create_task",
        summary="Buy groceries and milk",
        due_date="2025-10-28",
        confidence=1.0,
        raw_response='{"intent": "create_task", "summary": "Buy groceries and milk", "due_date": "2025-10-28"}'
    )
