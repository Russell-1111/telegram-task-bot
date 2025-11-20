"""
Outlook Service Module

This module provides a clean service layer for Microsoft Outlook Tasks integration
via Microsoft Graph API. It wraps the outlook_api module functions in a class-based
architecture for better testability and separation of concerns.

All methods are async to support non-blocking I/O operations.

Classes:
    OutlookService: Service class for managing Outlook tasks via Microsoft Graph API

Usage:
    outlook_service = OutlookService()
    token = await outlook_service.authenticate()
    task = await outlook_service.create_task(token, "Buy groceries", "2025-02-01T17:00:00.0000000")
    tasks = await outlook_service.get_uncompleted_tasks(token, max_tasks=10)
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any

# Import the underlying outlook_api module functions
import sys
from pathlib import Path

# Add parent directory to path if needed
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import outlook_api

# Configure logging
logger = logging.getLogger(__name__)


class OutlookService:
    """
    Service class for Microsoft Outlook Tasks integration with async I/O support.
    
    This class provides a clean interface to Microsoft Graph API for managing
    Outlook tasks. It wraps the outlook_api module functions with additional
    error handling, logging, and non-blocking I/O patterns.
    
    All methods are async and use asyncio.to_thread to wrap blocking operations
    for non-blocking execution.
    
    Attributes:
        None (stateless service)
        
    Methods:
        authenticate(): Initiates device code flow authentication (async)
        create_task(): Creates a new task in Outlook (async)
        update_task_due_date(): Updates the due date of an existing task (async)
        get_uncompleted_tasks(): Retrieves uncompleted tasks (async)
        get_all_tasks(): Retrieves all tasks from default list (async)
        delete_task(): Deletes a specific task by ID (async)
    """
    
    def __init__(self):
        """
        Initialize the OutlookService.
        
        This service is stateless and doesn't maintain any instance variables.
        All operations require an access token to be passed in.
        """
        logger.info("OutlookService initialized")
    
    async def authenticate(self) -> str:
        """
        Initiate device code flow authentication with Microsoft (async).
        
        This method starts the OAuth device code flow, which displays a code
        and URL for the user to visit and authenticate. After successful
        authentication, it returns an access token.
        
        This operation is run in a thread pool to avoid blocking the event loop.
        
        Returns:
            str: Microsoft Graph API access token
            
        Raises:
            ValueError: If device flow initiation fails
            Exception: If token acquisition fails
            
        Example:
            >>> outlook_service = OutlookService()
            >>> token = await outlook_service.authenticate()
            >>> print("Authenticated successfully!")
        """
        logger.info("Starting authentication flow (async)")
        try:
            # Run blocking operation in thread pool
            token = await asyncio.to_thread(outlook_api.get_auth_token)
            logger.info("Authentication completed successfully")
            return token
        except ValueError as e:
            logger.error(f"Device flow initiation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def create_task(
        self,
        access_token: str,
        task_title: str,
        due_date_iso: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task in the default Outlook task list (async).
        
        Args:
            access_token (str): Microsoft Graph API access token
            task_title (str): Title/name of the task to create
            due_date_iso (str, optional): Due date in ISO format with timezone
                Example: "2025-02-01T17:00:00.0000000"
                Timezone will be set to Asia/Kuala_Lumpur (UTC+8)
                
        Returns:
            dict: Task data returned from Microsoft Graph API containing:
                - id: Unique task identifier
                - title: Task title
                - status: Task status (notStarted, completed, etc.)
                - dueDateTime: Due date information (if provided)
                - Additional task metadata
                
        Raises:
            Exception: If task creation fails (network, API, or permission errors)
            
        Example:
            >>> service = OutlookService()
            >>> token = await service.authenticate()
            >>> task = await service.create_task(
            ...     token,
            ...     "Buy groceries",
            ...     "2025-02-01T17:00:00.0000000"
            ... )
            >>> print(f"Created task: {task['id']}")
        """
        logger.info(f"Creating task: '{task_title}' with due date: {due_date_iso} (async)")
        try:
            # Run blocking operation in thread pool
            task_data = await asyncio.to_thread(
                outlook_api.create_outlook_task,
                access_token,
                task_title,
                due_date_iso
            )
            logger.info(f"Task created successfully: {task_data['id']}")
            return task_data
        except Exception as e:
            logger.error(f"Failed to create task '{task_title}': {e}")
            raise
    
    async def update_task_due_date(
        self,
        access_token: str,
        task_id: str,
        new_due_date_iso: str
    ) -> Dict[str, Any]:
        """
        Update the due date of an existing Outlook task (async).
        
        Args:
            access_token (str): Microsoft Graph API access token
            task_id (str): Unique identifier of the task to update
            new_due_date_iso (str): New due date in ISO format
                Example: "2025-02-01T17:00:00.0000000"
                Timezone will be set to Asia/Kuala_Lumpur (UTC+8)
                
        Returns:
            dict: Updated task data from Microsoft Graph API
            
        Raises:
            ValueError: If datetime format is invalid
            Exception: If task not found or update fails
            
        Example:
            >>> service = OutlookService()
            >>> token = await service.authenticate()
            >>> updated_task = await service.update_task_due_date(
            ...     token,
            ...     "AAMkAG...",
            ...     "2025-02-15T17:00:00.0000000"
            ... )
        """
        logger.info(f"Updating task {task_id} with new due date: {new_due_date_iso} (async)")
        try:
            # Run blocking operation in thread pool
            updated_task = await asyncio.to_thread(
                outlook_api.update_task_due_date,
                access_token,
                task_id,
                new_due_date_iso
            )
            logger.info(f"Task {task_id} updated successfully")
            return updated_task
        except ValueError as e:
            logger.error(f"Invalid date format for task {task_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    async def get_uncompleted_tasks(
        self,
        access_token: str,
        max_tasks: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve uncompleted tasks from the default Outlook task list (async).
        
        This method fetches tasks with status != 'completed', ordered by
        due date (ascending), with tasks without due dates appearing last.
        
        Args:
            access_token (str): Microsoft Graph API access token
            max_tasks (int, optional): Maximum number of tasks to return.
                Default is 10. Microsoft Graph API supports pagination
                for larger datasets.
                
        Returns:
            list: List of task dictionaries, each containing:
                - id: Task identifier
                - title: Task title
                - status: Task status
                - dueDateTime: Due date info (if set)
                - Other task metadata
                
        Raises:
            Exception: If retrieval fails (network, API, or permission errors)
            
        Example:
            >>> service = OutlookService()
            >>> token = await service.authenticate()
            >>> tasks = await service.get_uncompleted_tasks(token, max_tasks=5)
            >>> for task in tasks:
            ...     print(f"{task['title']} - Due: {task.get('dueDateTime')}")
        """
        logger.info(f"Retrieving up to {max_tasks} uncompleted tasks (async)")
        try:
            # Run blocking operation in thread pool
            tasks = await asyncio.to_thread(
                outlook_api.get_uncompleted_tasks,
                access_token,
                max_tasks
            )
            logger.info(f"Retrieved {len(tasks)} uncompleted tasks")
            return tasks
        except Exception as e:
            logger.error(f"Failed to retrieve uncompleted tasks: {e}")
            raise
    
    async def get_all_tasks(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks from the default Outlook task list (async).
        
        This method fetches all tasks regardless of completion status.
        Note: This may return a large number of tasks. Consider using
        get_uncompleted_tasks() for better performance.
        
        Args:
            access_token (str): Microsoft Graph API access token
            
        Returns:
            list: List of all task dictionaries from the default list
            
        Raises:
            Exception: If retrieval fails
            
        Example:
            >>> service = OutlookService()
            >>> token = await service.authenticate()
            >>> all_tasks = await service.get_all_tasks(token)
            >>> print(f"Total tasks: {len(all_tasks)}")
        """
        logger.info("Retrieving all tasks from default list (async)")
        try:
            # Run blocking operation in thread pool
            tasks = await asyncio.to_thread(
                outlook_api.get_all_tasks,
                access_token
            )
            logger.info(f"Retrieved {len(tasks)} total tasks")
            return tasks
        except Exception as e:
            logger.error(f"Failed to retrieve all tasks: {e}")
            raise
    
    async def delete_task(self, access_token: str, task_id: str) -> bool:
        """
        Delete a specific task by its ID (async).
        
        Args:
            access_token (str): Microsoft Graph API access token
            task_id (str): Unique identifier of the task to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            Exception: If deletion fails (task not found, network error, etc.)
            
        Example:
            >>> service = OutlookService()
            >>> token = await service.authenticate()
            >>> await service.delete_task(token, "AAMkAG...")
            >>> print("Task deleted successfully")
        """
        logger.info(f"Deleting task: {task_id} (async)")
        try:
            # Run blocking operation in thread pool
            result = await asyncio.to_thread(
                outlook_api.delete_task,
                access_token,
                task_id
            )
            logger.info(f"Task {task_id} deleted successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise
