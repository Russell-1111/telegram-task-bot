"""
State Manager Module

This module provides centralized state management for user-specific data
across the Telegram bot session. It handles storing and retrieving user
context like last created tasks for due date updates.

Classes:
    UserStateManager: Manages user-specific state across bot sessions

Usage:
    state_manager = UserStateManager()
    state_manager.set_user_task(user_id, task_id, "Buy groceries", "2025-02-01")
    last_task = state_manager.get_user_task(user_id)
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class UserStateManager:
    """
    Manages user-specific state for the Telegram bot.
    
    This class provides a centralized way to store and retrieve user context,
    particularly the last created task for each user (used for due date updates).
    State is stored in memory and cleared when the bot restarts.
    
    Attributes:
        _user_tasks (dict): Internal dictionary storing user task state
            Format: {user_id: {
                "id": task_id,
                "title": task_title,
                "due_date": due_date,
                "created_at": datetime
            }}
    
    Methods:
        set_user_task(): Store user's last created task
        get_user_task(): Retrieve user's last task info
        clear_user_task(): Remove user's stored task
        has_user_task(): Check if user has a stored task
        get_all_users(): Get list of all user IDs with stored state
    """
    
    def __init__(self):
        """
        Initialize the UserStateManager.
        
        Creates an empty internal dictionary to store user task state.
        In the future, this could be extended to persist state to disk/database.
        """
        self._user_tasks: Dict[int, Dict[str, Any]] = {}
        logger.info("UserStateManager initialized")
    
    def set_user_task(
        self,
        user_id: int,
        task_id: str,
        task_title: str,
        due_date: Optional[str] = None
    ) -> None:
        """
        Store the user's last created task for potential due date updates.
        
        This method saves task information for a specific user, allowing
        the bot to reference it later when the user wants to update the
        due date without specifying which task.
        
        Args:
            user_id (int): Telegram user ID
            task_id (str): Outlook task ID (returned from Microsoft Graph API)
            task_title (str): Task title/summary
            due_date (str, optional): Due date in YYYY-MM-DD format
                If None, the task has no due date set.
                
        Returns:
            None
            
        Example:
            >>> state_manager = UserStateManager()
            >>> state_manager.set_user_task(
            ...     user_id=123456,
            ...     task_id="AAMkAG...",
            ...     task_title="Buy groceries",
            ...     due_date="2025-02-01"
            ... )
        """
        self._user_tasks[user_id] = {
            "id": task_id,
            "title": task_title,
            "due_date": due_date,
            "created_at": datetime.now()
        }
        logger.info(
            f"Stored task for user {user_id}: '{task_title}' "
            f"(ID: {task_id}, due: {due_date})"
        )
    
    def get_user_task(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve the user's last created task information.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            dict or None: Dictionary containing task info if found:
                {
                    "id": str - Outlook task ID
                    "title": str - Task title
                    "due_date": str or None - Due date in YYYY-MM-DD format
                    "created_at": datetime - When the task was stored
                }
                Returns None if no task is stored for this user.
                
        Example:
            >>> state_manager = UserStateManager()
            >>> last_task = state_manager.get_user_task(123456)
            >>> if last_task:
            ...     print(f"Last task: {last_task['title']}")
            ... else:
            ...     print("No task stored for this user")
        """
        task_info = self._user_tasks.get(user_id, None)
        if task_info:
            logger.debug(f"Retrieved task for user {user_id}: {task_info['title']}")
        else:
            logger.debug(f"No stored task for user {user_id}")
        return task_info
    
    def clear_user_task(self, user_id: int) -> bool:
        """
        Remove the stored task for a specific user.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            bool: True if a task was removed, False if no task was stored
            
        Example:
            >>> state_manager = UserStateManager()
            >>> was_cleared = state_manager.clear_user_task(123456)
            >>> if was_cleared:
            ...     print("Task cleared")
            ... else:
            ...     print("No task to clear")
        """
        if user_id in self._user_tasks:
            task_title = self._user_tasks[user_id].get("title", "Unknown")
            del self._user_tasks[user_id]
            logger.info(f"Cleared task for user {user_id}: '{task_title}'")
            return True
        else:
            logger.debug(f"No task to clear for user {user_id}")
            return False
    
    def has_user_task(self, user_id: int) -> bool:
        """
        Check if a user has a stored task.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            bool: True if user has a stored task, False otherwise
            
        Example:
            >>> state_manager = UserStateManager()
            >>> if state_manager.has_user_task(123456):
            ...     print("User has a stored task")
        """
        return user_id in self._user_tasks
    
    def get_all_users(self) -> list[int]:
        """
        Get a list of all user IDs with stored state.
        
        Useful for debugging or admin features to see which users
        have active task state.
        
        Returns:
            list: List of user IDs (integers) with stored tasks
            
        Example:
            >>> state_manager = UserStateManager()
            >>> users = state_manager.get_all_users()
            >>> print(f"Users with stored tasks: {len(users)}")
        """
        return list(self._user_tasks.keys())
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about stored state.
        
        Returns:
            dict: Statistics with keys:
                - total_users: Number of users with stored tasks
                - total_tasks: Total number of stored tasks
                
        Example:
            >>> state_manager = UserStateManager()
            >>> stats = state_manager.get_stats()
            >>> print(f"Total users: {stats['total_users']}")
        """
        return {
            "total_users": len(self._user_tasks),
            "total_tasks": len(self._user_tasks)  # Currently 1:1 mapping
        }
