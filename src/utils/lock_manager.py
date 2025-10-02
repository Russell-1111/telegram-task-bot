"""
Lock Manager for Bot Process Control

Manages single-instance bot execution via lock files to prevent
409 Conflict errors from multiple bot instances accessing the same
Telegram Bot API token simultaneously.
"""
import os
import sys
import logging
import subprocess
import atexit
import signal
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BotLockManager:
    """
    Manages single-instance bot execution via lock files.
    
    This class ensures only one bot instance runs at a time by:
    1. Creating a lock file with the current process ID
    2. Checking for stale locks from crashed processes
    3. Preventing new instances if an active instance exists
    4. Automatically cleaning up on exit
    
    Example:
        lock_manager = BotLockManager("bot.lock")
        if not lock_manager.acquire_lock():
            print("Another instance is running!")
            sys.exit(1)
        
        # ... run bot ...
        
        lock_manager.release_lock()  # Cleanup
    """
    
    def __init__(self, lock_file_path: str = "bot.lock"):
        """
        Initialize the lock manager
        
        Args:
            lock_file_path: Path to the lock file (default: "bot.lock")
        """
        self.lock_file_path = Path(lock_file_path)
        self.current_pid = os.getpid()
        self._lock_acquired = False
    
    def acquire_lock(self) -> bool:
        """
        Attempt to acquire the bot lock.
        
        Returns:
            True if lock was successfully acquired
            False if another instance is already running
        """
        if self.lock_file_path.exists():
            if not self._is_lock_stale():
                # Active lock exists
                try:
                    existing_pid = int(self.lock_file_path.read_text().strip())
                    logger.error(f"❌ Bot is already running with PID {existing_pid}")
                    logger.error(
                        "Please stop the existing instance first or delete "
                        f"{self.lock_file_path} if no bot is running."
                    )
                except (ValueError, FileNotFoundError):
                    logger.error("❌ Invalid lock file exists")
                return False
            
            # Stale lock detected - remove it
            logger.warning(f"Stale lock detected, removing...")
            self.release_lock()
        
        # Create new lock
        self._create_lock()
        self._register_cleanup_handlers()
        return True
    
    def release_lock(self):
        """Release the bot lock by removing the lock file"""
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
                logger.info(f"Lock file removed: {self.lock_file_path}")
                self._lock_acquired = False
        except Exception as e:
            logger.error(f"Error removing lock file: {e}")
    
    def _is_lock_stale(self) -> bool:
        """
        Check if the existing lock belongs to a dead process.
        
        Returns:
            True if the lock is stale (process not running)
            False if the process is still active
        """
        try:
            # Read PID from lock file
            pid = int(self.lock_file_path.read_text().strip())
            
            # Check if process is running (Windows-specific)
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                shell=True
            )
            
            # Check if the process actually exists in the output
            # Look for both the PID and "python" in the output
            output_lower = result.stdout.lower()
            if "python" in output_lower and str(pid) in result.stdout:
                logger.info(f"Active bot process found with PID {pid}")
                return False  # Process is running
            else:
                logger.info(f"Stale lock detected: PID {pid} no longer running")
                return True  # Process is not running
        
        except subprocess.CalledProcessError:
            logger.warning(f"Could not check process status, assuming stale")
            return True  # Assume stale if we can't verify
        except (ValueError, FileNotFoundError) as e:
            logger.warning(f"Error reading lock file: {e}, assuming stale")
            return True  # Invalid lock file, assume stale
        except Exception as e:
            logger.error(f"Unexpected error checking lock: {e}")
            return True  # On error, assume stale to allow startup
    
    def _create_lock(self):
        """Create lock file with current process ID"""
        try:
            self.lock_file_path.write_text(str(self.current_pid))
            logger.info(f"Lock acquired: PID {self.current_pid}")
            self._lock_acquired = True
        except Exception as e:
            logger.error(f"Failed to create lock file: {e}")
            raise
    
    def _register_cleanup_handlers(self):
        """Register cleanup handlers for graceful shutdown"""
        # Register atexit handler
        atexit.register(self.release_lock)
        
        # Register signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            """Handle shutdown signals gracefully"""
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.release_lock()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
            signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        except (ValueError, OSError) as e:
            # Signal handling might not work in all environments (e.g., Windows)
            logger.warning(f"Could not register signal handlers: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        if not self.acquire_lock():
            raise RuntimeError("Could not acquire bot lock - another instance is running")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release_lock()
        return False  # Don't suppress exceptions
    
    def __del__(self):
        """Cleanup on object destruction"""
        if self._lock_acquired:
            self.release_lock()
