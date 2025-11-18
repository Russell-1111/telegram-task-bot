"""
Auto-save thread for periodic state persistence.

This module provides background thread functionality to automatically save
bot state at regular intervals, ensuring minimal data loss in case of crashes
or unexpected shutdowns.

Features:
- Configurable save interval (default: 5 minutes)
- Skip unchanged state (hash-based tracking)
- Graceful shutdown support
- Exception handling to prevent thread crashes
- Comprehensive logging

Classes:
    AutoSaveThread: Background thread for periodic state saving
"""

import logging
import threading
import time
import hashlib
import json
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoSaveThread(threading.Thread):
    """
    Background thread that periodically saves state to disk.
    
    Features:
    - Runs in background without blocking main thread
    - Configurable save interval (seconds)
    - Tracks last saved state hash to skip unnecessary saves
    - Graceful shutdown via threading.Event
    - Exception handling to prevent crashes
    - Comprehensive logging with timestamps
    
    Attributes:
        token_manager: TokenManager instance to save token state
        state_manager: UserStateManager instance to save user state
        interval_seconds: Time between save operations (default: 300 seconds = 5 minutes)
        _stop_event: threading.Event to signal shutdown
        _last_token_hash: Hash of last saved token state
        _last_state_hash: Hash of last saved user state
        daemon: Thread runs as daemon (exits when main program exits)
    
    Example:
        ```python
        auto_save = AutoSaveThread(token_manager, state_manager, interval_seconds=300)
        auto_save.start()
        
        # Later, during shutdown:
        auto_save.stop()
        auto_save.join(timeout=5)
        ```
    """
    
    def __init__(self, token_manager, state_manager, interval_seconds: int = 300):
        """
        Initialize auto-save thread.
        
        Args:
            token_manager: TokenManager instance for token persistence
            state_manager: UserStateManager instance for state persistence
            interval_seconds: Time between save operations (default: 300 = 5 minutes)
        
        Raises:
            ValueError: If interval_seconds is less than 1
        """
        super().__init__(daemon=True, name="AutoSaveThread")
        
        if interval_seconds < 1:
            raise ValueError(f"interval_seconds must be >= 1, got {interval_seconds}")
        
        self.token_manager = token_manager
        self.state_manager = state_manager
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._last_token_hash: Optional[str] = None
        self._last_state_hash: Optional[str] = None
        
        logger.info(f"AutoSaveThread initialized with {interval_seconds}s interval")
    
    def run(self):
        """
        Main thread loop - periodically save state.
        
        This method runs in the background thread. It:
        1. Waits for the configured interval (or stop signal)
        2. Computes hash of current state
        3. Skips save if state unchanged
        4. Saves state if changed
        5. Updates last saved hash
        6. Handles exceptions without crashing
        
        The loop exits when stop() is called or an unrecoverable error occurs.
        """
        logger.info("AutoSaveThread started")
        
        while not self._stop_event.is_set():
            # Wait for interval or stop signal (whichever comes first)
            if self._stop_event.wait(timeout=self.interval_seconds):
                # Stop signal received
                logger.info("AutoSaveThread received stop signal")
                break
            
            # Time to save state
            try:
                self._perform_save()
            except Exception as e:
                logger.error(f"AutoSaveThread error during save: {e}", exc_info=True)
                # Continue running despite error
        
        logger.info("AutoSaveThread stopped")
    
    def _perform_save(self):
        """
        Perform the actual save operation with change detection.
        
        This method:
        1. Computes hash of current token state
        2. Computes hash of current user state
        3. Compares with last saved hashes
        4. Saves only if changed
        5. Updates last saved hashes
        
        Hash-based change detection prevents unnecessary disk I/O
        and backup rotation when state hasn't changed.
        """
        saved_something = False
        start_time = time.time()
        
        # Save token state if changed
        try:
            current_token_hash = self._compute_token_hash()
            if current_token_hash != self._last_token_hash:
                if self.token_manager.save_state():
                    self._last_token_hash = current_token_hash
                    saved_something = True
                    logger.debug("AutoSave: Token state saved (changed)")
                else:
                    logger.warning("AutoSave: Token state save failed")
            else:
                logger.debug("AutoSave: Token state unchanged, skipped")
        except Exception as e:
            logger.error(f"AutoSave: Error saving token state: {e}")
        
        # Save user state if changed
        try:
            current_state_hash = self._compute_state_hash()
            if current_state_hash != self._last_state_hash:
                if self.state_manager.save_state():
                    self._last_state_hash = current_state_hash
                    saved_something = True
                    logger.debug("AutoSave: User state saved (changed)")
                else:
                    logger.warning("AutoSave: User state save failed")
            else:
                logger.debug("AutoSave: User state unchanged, skipped")
        except Exception as e:
            logger.error(f"AutoSave: Error saving user state: {e}")
        
        elapsed = time.time() - start_time
        
        if saved_something:
            logger.info(f"AutoSave: State saved in {elapsed:.3f}s at {datetime.now().isoformat()}")
        else:
            logger.debug(f"AutoSave: No changes detected in {elapsed:.3f}s")
    
    def _compute_token_hash(self) -> str:
        """
        Compute hash of current token state.
        
        Returns:
            str: SHA256 hash of token state (hex string)
        
        Note:
            Returns "empty" if no token exists or computation fails.
        """
        try:
            token = self.token_manager.get_token()
            if not token:
                return "empty"
            
            # Hash the token itself
            return hashlib.sha256(token.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error computing token hash: {e}")
            return "error"
    
    def _compute_state_hash(self) -> str:
        """
        Compute hash of current user state.
        
        Returns:
            str: SHA256 hash of user state (hex string)
        
        Note:
            Returns "empty" if no state exists or computation fails.
            Serializes state to JSON for consistent hashing.
        """
        try:
            # Access internal state (needs to be accessible from manager)
            if not hasattr(self.state_manager, '_user_tasks'):
                return "empty"
            
            user_tasks = self.state_manager._user_tasks
            if not user_tasks:
                return "empty"
            
            # Serialize to JSON for consistent hashing
            # Sort keys to ensure consistent ordering
            state_json = json.dumps(user_tasks, sort_keys=True, default=str)
            return hashlib.sha256(state_json.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error computing state hash: {e}")
            return "error"
    
    def stop(self, timeout: float = 5.0):
        """
        Stop the auto-save thread gracefully.
        
        This method:
        1. Signals the thread to stop via _stop_event
        2. Waits for thread to finish (with timeout)
        3. Performs a final save operation
        
        Args:
            timeout: Maximum time to wait for thread to stop (seconds)
        
        Note:
            Always call this before program exit to ensure final save.
        """
        logger.info("Stopping AutoSaveThread...")
        self._stop_event.set()
        
        # Wait for thread to finish
        self.join(timeout=timeout)
        
        if self.is_alive():
            logger.warning(f"AutoSaveThread did not stop within {timeout}s timeout")
        else:
            logger.info("AutoSaveThread stopped cleanly")
        
        # Perform final save
        try:
            logger.info("Performing final auto-save...")
            self._perform_save()
        except Exception as e:
            logger.error(f"Error during final auto-save: {e}")
    
    def get_status(self) -> dict:
        """
        Get current status of auto-save thread.
        
        Returns:
            dict: Status information including:
                - is_alive: Whether thread is running
                - interval_seconds: Configured save interval
                - last_token_hash: Hash of last saved token state
                - last_state_hash: Hash of last saved user state
        
        Example:
            ```python
            status = auto_save.get_status()
            print(f"Thread running: {status['is_alive']}")
            print(f"Interval: {status['interval_seconds']}s")
            ```
        """
        return {
            'is_alive': self.is_alive(),
            'interval_seconds': self.interval_seconds,
            'last_token_hash': self._last_token_hash,
            'last_state_hash': self._last_state_hash,
        }
