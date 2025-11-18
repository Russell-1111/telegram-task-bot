"""
State Manager Module

This module provides centralized state management for user-specific data
across the Telegram bot session. It handles storing and retrieving user
context like last created tasks for due date updates, with optional
persistence to disk.

Classes:
    UserStateManager: Manages user-specific state across bot sessions with persistence

Usage:
    # Without persistence (in-memory only)
    state_manager = UserStateManager()
    
    # With persistence
    state_manager = UserStateManager(
        state_file_path="data/user_state.json",
        persistence_enabled=True
    )
    state_manager.load_state()  # Load from disk on startup
    state_manager.set_user_task(user_id, task_id, "Buy groceries", "2025-02-01")  # Auto-saves
    state_manager.save_state()  # Explicit save on shutdown
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class UserStateManager:
    """
    Manages user-specific state for the Telegram bot with optional persistence.
    
    This class provides a centralized way to store and retrieve user context,
    particularly the last created task for each user (used for due date updates).
    Supports both in-memory storage and JSON file persistence.
    
    Attributes:
        _user_tasks (dict): Internal dictionary storing user task state
        _persistence_enabled (bool): Whether to persist state to disk
        _state_file_path (str): Path to JSON state file
    
    Methods:
        set_user_task(): Store user's last created task (auto-saves if persistence enabled)
        get_user_task(): Retrieve user's last task info
        clear_user_task(): Remove user's stored task
        has_user_task(): Check if user has a stored task
        get_all_users(): Get list of all user IDs with stored state
        load_state(): Load state from JSON file (call on startup)
        save_state(): Save state to JSON file (call on shutdown)
    """
    
    def __init__(
        self,
        state_file_path: str = "data/user_state.json",
        persistence_enabled: bool = False
    ):
        """
        Initialize the UserStateManager with optional persistence.
        
        Args:
            state_file_path (str): Path to save state JSON (default: "data/user_state.json")
            persistence_enabled (bool): Enable persistent storage (default: False)
        
        Example:
            >>> # In-memory only
            >>> state_manager = UserStateManager()
            
            >>> # With persistence
            >>> state_manager = UserStateManager("data/user_state.json", True)
        """
        self._user_tasks: Dict[int, Dict[str, Any]] = {}
        self._persistence_enabled = persistence_enabled
        self._state_file_path = state_file_path
        
        if self._persistence_enabled:
            logger.info(
                f"UserStateManager initialized with persistence: {self._state_file_path}"
            )
        else:
            logger.info("UserStateManager initialized (in-memory only)")
    
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
        
        # Auto-save if persistence is enabled
        if self._persistence_enabled:
            self._save_to_disk()
    
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
    
    def _save_to_disk(self) -> bool:
        """
        Save state to JSON file (private method, called automatically).
        
        Returns:
            bool: True if save succeeded, False otherwise
        """
        if not self._persistence_enabled:
            return False
        
        try:
            from .file_operations import safe_json_save
            
            # Prepare data to save
            users_data = {}
            for user_id, task_info in self._user_tasks.items():
                users_data[str(user_id)] = {
                    "id": task_info["id"],
                    "title": task_info["title"],
                    "due_date": task_info["due_date"],
                    "created_at": task_info["created_at"].isoformat() if isinstance(task_info["created_at"], datetime) else task_info["created_at"]
                }
            
            data = {
                "version": "1.0",
                "users": users_data,
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "user_count": len(users_data)
                }
            }
            
            # Save using safe_json_save (handles atomic writes and backups)
            success = safe_json_save(self._state_file_path, data)
            
            if success:
                logger.info(
                    f"User state saved: {len(users_data)} users to {self._state_file_path}"
                )
            return success
            
        except Exception as e:
            logger.error(f"Failed to save user state to disk: {e}", exc_info=True)
            return False
    
    def _load_from_disk(self) -> bool:
        """
        Load state from JSON file (private method).
        
        Returns:
            bool: True if load succeeded, False otherwise
        """
        if not self._persistence_enabled:
            return False
        
        try:
            from .file_operations import safe_json_load
            
            data = safe_json_load(self._state_file_path)
            
            if data is None:
                logger.info(f"No state file found or file is empty: {self._state_file_path}")
                return False
            
            # Parse version (for future schema migrations)
            version = data.get("version", "1.0")
            if version != "1.0":
                logger.warning(f"Unknown state file version: {version}, attempting to parse anyway")
            
            # Restore user tasks
            users_data = data.get("users", {})
            self._user_tasks = {}
            
            for user_id_str, task_info in users_data.items():
                try:
                    user_id = int(user_id_str)
                    created_at_str = task_info.get("created_at")
                    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
                    
                    self._user_tasks[user_id] = {
                        "id": task_info["id"],
                        "title": task_info["title"],
                        "due_date": task_info.get("due_date"),
                        "created_at": created_at
                    }
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid user entry {user_id_str}: {e}")
                    continue
            
            logger.info(
                f"User state loaded: {len(self._user_tasks)} users from {self._state_file_path}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load user state from disk: {e}", exc_info=True)
            return False
    
    def load_state(self) -> bool:
        """
        Load state from JSON file (call on bot startup).
        
        Returns:
            bool: True if state loaded successfully, False otherwise
        
        Example:
            >>> state_manager = UserStateManager("data/user_state.json", True)
            >>> if state_manager.load_state():
            ...     print(f"Restored state for {len(state_manager.get_all_users())} users")
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping load_state")
            return False
        
        return self._load_from_disk()
    
    def save_state(self) -> bool:
        """
        Save state to JSON file (call on bot shutdown).
        
        Returns:
            bool: True if state saved successfully, False otherwise
        
        Example:
            >>> state_manager.save_state()  # Save before shutdown
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping save_state")
            return False
        
        return self._save_to_disk()
