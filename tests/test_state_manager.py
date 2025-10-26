"""
Unit tests for UserStateManager

Tests cover:
- Setting user task state
- Getting user task state
- Clearing user task state
- Checking if user has task
- Getting all users with state
- Statistics retrieval
"""
import pytest
from datetime import datetime
from utils.state_manager import UserStateManager


class TestUserStateManager:
    """Test suite for UserStateManager class"""
    
    def test_initialization(self):
        """Test that StateManager initializes with empty state"""
        manager = UserStateManager()
        assert manager._user_tasks == {}
        assert manager.get_all_users() == []
    
    def test_set_user_task_basic(self):
        """Test setting a basic user task"""
        manager = UserStateManager()
        user_id = 123456
        task_id = "task_abc123"
        task_title = "Buy groceries"
        due_date = "2025-10-28"
        
        manager.set_user_task(user_id, task_id, task_title, due_date)
        
        assert manager.has_user_task(user_id)
        task_data = manager.get_user_task(user_id)
        assert task_data['id'] == task_id
        assert task_data['title'] == task_title
        assert task_data['due_date'] == due_date
        assert isinstance(task_data['created_at'], datetime)
    
    def test_set_user_task_without_due_date(self):
        """Test setting a task without due date"""
        manager = UserStateManager()
        user_id = 123456
        task_id = "task_xyz789"
        task_title = "Call dentist"
        
        manager.set_user_task(user_id, task_id, task_title, None)
        
        task_data = manager.get_user_task(user_id)
        assert task_data['due_date'] is None
        assert task_data['title'] == task_title
    
    def test_get_user_task_nonexistent(self):
        """Test getting task for user with no stored task"""
        manager = UserStateManager()
        result = manager.get_user_task(999999)
        assert result is None
    
    def test_has_user_task(self):
        """Test checking if user has task"""
        manager = UserStateManager()
        user_id = 123456
        
        assert not manager.has_user_task(user_id)
        
        manager.set_user_task(user_id, "task_123", "Test task", "2025-10-28")
        
        assert manager.has_user_task(user_id)
    
    def test_clear_user_task(self):
        """Test clearing user task state"""
        manager = UserStateManager()
        user_id = 123456
        
        # Set a task
        manager.set_user_task(user_id, "task_123", "Test task", "2025-10-28")
        assert manager.has_user_task(user_id)
        
        # Clear it
        result = manager.clear_user_task(user_id)
        assert result is True
        assert not manager.has_user_task(user_id)
        assert manager.get_user_task(user_id) is None
    
    def test_clear_nonexistent_task(self):
        """Test clearing task for user with no task"""
        manager = UserStateManager()
        result = manager.clear_user_task(999999)
        assert result is False
    
    def test_get_all_users(self):
        """Test getting all users with stored state"""
        manager = UserStateManager()
        
        # Initially empty
        assert manager.get_all_users() == []
        
        # Add tasks for multiple users
        manager.set_user_task(111, "task_1", "Task 1", None)
        manager.set_user_task(222, "task_2", "Task 2", "2025-10-28")
        manager.set_user_task(333, "task_3", "Task 3", "2025-10-29")
        
        users = manager.get_all_users()
        assert len(users) == 3
        assert 111 in users
        assert 222 in users
        assert 333 in users
    
    def test_get_stats(self):
        """Test getting statistics about stored state"""
        manager = UserStateManager()
        
        # Initially empty
        stats = manager.get_stats()
        assert stats['total_users'] == 0
        assert stats['total_tasks'] == 0
        
        # Add some tasks
        manager.set_user_task(111, "task_1", "Task 1", None)
        manager.set_user_task(222, "task_2", "Task 2", "2025-10-28")
        
        stats = manager.get_stats()
        assert stats['total_users'] == 2
        assert stats['total_tasks'] == 2
    
    def test_update_existing_task(self):
        """Test updating an existing user's task"""
        manager = UserStateManager()
        user_id = 123456
        
        # Set initial task
        manager.set_user_task(user_id, "task_1", "Old task", "2025-10-28")
        
        # Update with new task
        manager.set_user_task(user_id, "task_2", "New task", "2025-10-30")
        
        # Should have replaced the old task
        task_data = manager.get_user_task(user_id)
        assert task_data['id'] == "task_2"
        assert task_data['title'] == "New task"
        assert task_data['due_date'] == "2025-10-30"
    
    def test_multiple_users_isolation(self):
        """Test that multiple users' tasks are kept separate"""
        manager = UserStateManager()
        
        user1_id = 111
        user2_id = 222
        
        manager.set_user_task(user1_id, "task_1", "User 1 Task", "2025-10-28")
        manager.set_user_task(user2_id, "task_2", "User 2 Task", "2025-10-29")
        
        # Each user should have their own task
        user1_task = manager.get_user_task(user1_id)
        user2_task = manager.get_user_task(user2_id)
        
        assert user1_task['title'] == "User 1 Task"
        assert user2_task['title'] == "User 2 Task"
        assert user1_task['id'] != user2_task['id']
