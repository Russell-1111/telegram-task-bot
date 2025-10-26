"""
Unit tests for task_formatter module

Tests cover:
- Individual task formatting
- Task list formatting
- Motivational message generation
- Emoji usage
- Edge cases (empty lists, overdue tasks, high priority)
"""
import pytest
from datetime import datetime, timedelta
import pytz
from formatters.task_formatter import (
    format_task_for_display,
    format_tasks_list,
    get_motivational_message
)


MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


class TestTaskFormatter:
    """Test suite for task formatter functions"""
    
    def test_format_task_basic(self, sample_outlook_task):
        """Test formatting a basic task"""
        result = format_task_for_display(sample_outlook_task, 1)
        
        assert "1. **Test Task**" in result
        assert "📅" in result  # Due date emoji
    
    def test_format_task_high_priority(self, sample_high_priority_task):
        """Test formatting a high priority task"""
        result = format_task_for_display(sample_high_priority_task, 1)
        
        assert "**Urgent Task**" in result
        assert "⚡" in result  # High priority emoji
        assert "**High Priority**" in result
    
    def test_format_task_overdue(self, sample_overdue_task):
        """Test formatting an overdue task"""
        result = format_task_for_display(sample_overdue_task, 1)
        
        assert "**Overdue Task**" in result
        assert "🔴" in result  # Overdue emoji
        assert "**Overdue**" in result
    
    def test_format_task_no_due_date(self):
        """Test formatting a task without due date"""
        task = {
            'title': 'Task without date',
            'status': 'notStarted',
            'importance': 'normal'
        }
        result = format_task_for_display(task, 1)
        
        assert "**Task without date**" in result
        # Should not have date-related emojis
        assert "📅" not in result
        assert "🔴" not in result
    
    def test_format_task_numbering(self):
        """Test that task numbering works correctly"""
        task = {'title': 'Test', 'status': 'notStarted', 'importance': 'normal'}
        
        result1 = format_task_for_display(task, 1)
        result5 = format_task_for_display(task, 5)
        result10 = format_task_for_display(task, 10)
        
        assert result1.startswith("1.")
        assert result5.startswith("5.")
        assert result10.startswith("10.")
    
    def test_format_tasks_list_empty(self):
        """Test formatting an empty task list"""
        result = format_tasks_list([])
        
        assert "📋 **Your Tasks**" in result
        assert "🎉" in result
        assert "Congratulations" in result
        assert "no pending tasks" in result.lower()
    
    def test_format_tasks_list_single(self, sample_outlook_task):
        """Test formatting a list with single task"""
        result = format_tasks_list([sample_outlook_task])
        
        assert "📋 **Your Current Tasks** (1 remaining)" in result
        assert "**Test Task**" in result
    
    def test_format_tasks_list_multiple(self, sample_outlook_task, sample_high_priority_task):
        """Test formatting a list with multiple tasks"""
        tasks = [sample_outlook_task, sample_high_priority_task]
        result = format_tasks_list(tasks)
        
        assert "📋 **Your Current Tasks** (2 remaining)" in result
        assert "1. **Test Task**" in result
        assert "2. **Urgent Task**" in result
    
    def test_get_motivational_message_zero_tasks(self):
        """Test motivational message for zero tasks"""
        message = get_motivational_message(0)
        
        # Check for any celebratory emoji  
        assert any(emoji in message for emoji in ["🎉", "🏆", "✨", "🎯", "🏖️"])
        # Check for accomplishment words
        assert any(word in message.lower() for word in ["amazing", "inbox zero", "perfect", "outstanding", "accomplished", "done", "break", "great"])
    
    def test_get_motivational_message_few_tasks(self):
        """Test motivational message for 1-3 tasks"""
        for count in [1, 2, 3]:
            message = get_motivational_message(count)
            
            assert str(count) in message
            assert any(emoji in message for emoji in ["💪", "🌟", "🎯", "🔥", "⚡"])
    
    def test_get_motivational_message_medium_tasks(self):
        """Test motivational message for 4-7 tasks"""
        for count in [4, 5, 6, 7]:
            message = get_motivational_message(count)
            
            assert str(count) in message
            assert any(emoji in message for emoji in ["💪", "🚀", "⭐", "🎯", "🌟"])
    
    def test_get_motivational_message_many_tasks(self):
        """Test motivational message for 8+ tasks"""
        for count in [8, 10, 15]:
            message = get_motivational_message(count)
            
            assert str(count) in message
            assert any(emoji in message for emoji in ["🎯", "🚀", "💫", "⚡", "🌈"])
    
    def test_get_motivational_message_with_overdue(self):
        """Test motivational message with overdue tasks"""
        message = get_motivational_message(5, overdue_count=2)
        
        assert "🔴" in message
        assert "overdue" in message.lower()
        assert "2 tasks" in message or "2" in message
    
    def test_get_motivational_message_single_overdue(self):
        """Test motivational message with single overdue task"""
        message = get_motivational_message(3, overdue_count=1)
        
        assert "🔴" in message
        assert "1 task" in message or "1" in message
        assert "it" in message  # Singular reference
    
    def test_get_motivational_message_randomness(self):
        """Test that messages are randomized"""
        messages = set()
        for _ in range(10):
            messages.add(get_motivational_message(5))
        
        # Should have gotten at least 2 different messages
        assert len(messages) > 1
    
    def test_format_task_markdown_safety(self):
        """Test that task formatting handles special markdown characters"""
        task = {
            'title': 'Task with *asterisks* and _underscores_',
            'status': 'notStarted',
            'importance': 'normal'
        }
        result = format_task_for_display(task, 1)
        
        # Should preserve the special characters
        assert '*asterisks*' in result
        assert '_underscores_' in result
