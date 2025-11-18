"""
Token Manager Module

This module provides centralized token management for Microsoft Outlook
authentication. It stores and retrieves access tokens across bot sessions
with optional encrypted persistence to disk.

Classes:
    TokenManager: Manages Microsoft Graph API access tokens with persistence

Usage:
    # Without persistence (in-memory only)
    token_manager = TokenManager()
    
    # With persistence
    from utils.encryption import EncryptionManager
    encryption_manager = EncryptionManager(key)
    token_manager = TokenManager(
        encryption_manager=encryption_manager,
        token_file_path="data/tokens.enc",
        persistence_enabled=True
    )
    token_manager.load_state()  # Load from disk on startup
    token_manager.set_token("eyJ0eXAiOiJKV1QiLCJub...")  # Auto-saves
    token_manager.save_state()  # Explicit save on shutdown
"""

import logging
import json
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages Microsoft Graph API access tokens with optional encrypted persistence.
    
    This class provides a centralized way to store and retrieve Outlook
    access tokens. Supports both in-memory storage and encrypted disk persistence
    for seamless bot restarts without re-authentication.
    
    Attributes:
        _access_token (str or None): The stored access token
        _token_set_at (datetime or None): Timestamp when token was set
        _persistence_enabled (bool): Whether to persist state to disk
        _encryption_manager (EncryptionManager or None): For token encryption
        _token_file_path (str): Path to encrypted token file
    
    Methods:
        set_token(): Store an access token (auto-saves if persistence enabled)
        get_token(): Retrieve the stored token
        clear_token(): Remove the stored token
        has_token(): Check if a token is stored
        get_token_age(): Get the age of the stored token in seconds
        load_state(): Load token from encrypted file (call on startup)
        save_state(): Save token to encrypted file (call on shutdown)
    """
    
    def __init__(
        self,
        encryption_manager: Optional['EncryptionManager'] = None,
        token_file_path: str = "data/tokens.enc",
        persistence_enabled: bool = False
    ):
        """
        Initialize the TokenManager with optional persistence.
        
        Args:
            encryption_manager (EncryptionManager, optional): For encrypting tokens
            token_file_path (str): Path to save encrypted tokens (default: "data/tokens.enc")
            persistence_enabled (bool): Enable persistent storage (default: False)
        
        Example:
            >>> # In-memory only
            >>> token_manager = TokenManager()
            
            >>> # With persistence
            >>> from utils.encryption import EncryptionManager
            >>> enc = EncryptionManager(key)
            >>> token_manager = TokenManager(enc, "data/tokens.enc", True)
        """
        self._access_token: Optional[str] = None
        self._token_set_at: Optional[datetime] = None
        self._persistence_enabled = persistence_enabled
        self._encryption_manager = encryption_manager
        self._token_file_path = token_file_path
        
        if self._persistence_enabled:
            if not self._encryption_manager:
                logger.warning(
                    "Persistence enabled but no encryption_manager provided. "
                    "Disabling persistence."
                )
                self._persistence_enabled = False
            else:
                logger.info(
                    f"TokenManager initialized with persistence: {self._token_file_path}"
                )
        else:
            logger.info("TokenManager initialized (in-memory only)")
    
    def set_token(self, token: str) -> None:
        """
        Store an access token.
        
        This method saves the Microsoft Graph API access token obtained
        from the device code flow authentication. The token is stored
        with a timestamp for age tracking.
        
        Args:
            token (str): Microsoft Graph API access token
                Example: "eyJ0eXAiOiJKV1QiLCJub..."
                
        Returns:
            None
            
        Example:
            >>> token_manager = TokenManager()
            >>> token_manager.set_token("eyJ0eXAiOiJKV1QiLCJub...")
            >>> print("Token stored successfully")
        """
        self._access_token = token
        self._token_set_at = datetime.now()
        logger.info(
            f"Access token stored (length: {len(token)} chars, "
            f"set at: {self._token_set_at.isoformat()})"
        )
        
        # Auto-save if persistence is enabled
        if self._persistence_enabled:
            self._save_to_disk()
    
    def get_token(self) -> Optional[str]:
        """
        Retrieve the stored access token.
        
        Returns:
            str or None: The stored access token if available, None otherwise
            
        Example:
            >>> token_manager = TokenManager()
            >>> token = token_manager.get_token()
            >>> if token:
            ...     print("Using stored token")
            ... else:
            ...     print("No token available, need to authenticate")
        """
        if self._access_token:
            logger.debug(
                f"Retrieved access token (length: {len(self._access_token)} chars)"
            )
        else:
            logger.debug("No access token available")
        return self._access_token
    
    def clear_token(self) -> bool:
        """
        Remove the stored access token.
        
        Useful when logging out or when a token expires/becomes invalid.
        
        Returns:
            bool: True if a token was cleared, False if no token was stored
            
        Example:
            >>> token_manager = TokenManager()
            >>> was_cleared = token_manager.clear_token()
            >>> if was_cleared:
            ...     print("Token cleared")
        """
        if self._access_token:
            token_length = len(self._access_token)
            self._access_token = None
            self._token_set_at = None
            logger.info(f"Access token cleared (was {token_length} chars)")
            return True
        else:
            logger.debug("No token to clear")
            return False
    
    def has_token(self) -> bool:
        """
        Check if an access token is stored.
        
        Returns:
            bool: True if a token is stored, False otherwise
            
        Example:
            >>> token_manager = TokenManager()
            >>> if not token_manager.has_token():
            ...     print("Please authenticate first")
        """
        return self._access_token is not None
    
    def get_token_age(self) -> Optional[float]:
        """
        Get the age of the stored token in seconds.
        
        Useful for implementing token refresh logic or warning users
        about expired tokens. Microsoft Graph tokens typically expire
        after 1 hour.
        
        Returns:
            float or None: Token age in seconds if token is stored,
                None if no token is available
            
        Example:
            >>> token_manager = TokenManager()
            >>> age = token_manager.get_token_age()
            >>> if age and age > 3600:
            ...     print("Token may be expired (>1 hour old)")
        """
        if self._token_set_at is None:
            logger.debug("Cannot calculate token age - no token stored")
            return None
        
        age_seconds = (datetime.now() - self._token_set_at).total_seconds()
        logger.debug(f"Token age: {age_seconds:.2f} seconds")
        return age_seconds
    
    def get_token_info(self) -> dict:
        """
        Get information about the stored token.
        
        Returns:
            dict: Dictionary containing:
                - has_token (bool): Whether a token is stored
                - token_length (int or None): Length of token string
                - token_age_seconds (float or None): Age in seconds
                - set_at (str or None): ISO format timestamp when set
                
        Example:
            >>> token_manager = TokenManager()
            >>> info = token_manager.get_token_info()
            >>> print(f"Token info: {info}")
        """
        return {
            "has_token": self.has_token(),
            "token_length": len(self._access_token) if self._access_token else None,
            "token_age_seconds": self.get_token_age(),
            "set_at": self._token_set_at.isoformat() if self._token_set_at else None
        }
    
    def _save_to_disk(self) -> bool:
        """
        Save token to encrypted file (private method, called automatically).
        
        Returns:
            bool: True if save succeeded, False otherwise
        """
        if not self._persistence_enabled:
            return False
        
        if not self._access_token:
            logger.debug("No token to save")
            return False
        
        try:
            from .file_operations import rotate_backups, atomic_write
            
            # Prepare data to save
            data = {
                "version": "1.0",
                "access_token": self._access_token,
                "token_set_at": self._token_set_at.isoformat() if self._token_set_at else None,
                "metadata": {
                    "encrypted_at": datetime.now().isoformat()
                }
            }
            
            # Serialize to JSON
            json_data = json.dumps(data)
            
            # Encrypt
            encrypted_data = self._encryption_manager.encrypt(json_data)
            
            # Rotate backups before saving
            rotate_backups(self._token_file_path, retention=3)
            
            # Atomic write (writes bytes directly)
            filepath_obj = Path(self._token_file_path)
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
            
            temp_file = filepath_obj.with_suffix(filepath_obj.suffix + '.tmp')
            temp_file.write_bytes(encrypted_data)
            
            from .file_operations import set_secure_permissions
            set_secure_permissions(str(temp_file))
            
            temp_file.replace(filepath_obj)
            
            logger.info(f"Token saved to encrypted file: {self._token_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save token to disk: {e}", exc_info=True)
            return False
    
    def _load_from_disk(self) -> bool:
        """
        Load token from encrypted file (private method).
        
        Returns:
            bool: True if load succeeded, False otherwise
        """
        if not self._persistence_enabled:
            return False
        
        try:
            filepath_obj = Path(self._token_file_path)
            
            if not filepath_obj.exists():
                logger.info(f"No token file found: {self._token_file_path}")
                return False
            
            # Read encrypted data
            encrypted_data = filepath_obj.read_bytes()
            
            # Decrypt
            json_data = self._encryption_manager.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(json_data)
            
            # Restore token
            self._access_token = data.get("access_token")
            token_set_at_str = data.get("token_set_at")
            if token_set_at_str:
                self._token_set_at = datetime.fromisoformat(token_set_at_str)
            
            logger.info(
                f"Token loaded from encrypted file: {self._token_file_path} "
                f"(set at: {self._token_set_at.isoformat() if self._token_set_at else 'unknown'})"
            )
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error loading token: {e}")
            self._backup_corrupted_file("json_error")
            return False
            
        except Exception as e:
            # Could be decryption error (wrong key, corrupted data)
            logger.error(f"Failed to load token from disk: {e}")
            if "InvalidToken" in str(type(e).__name__):
                logger.error(
                    "Decryption failed - wrong encryption key or corrupted file. "
                    "Token will need to be re-authenticated."
                )
            self._backup_corrupted_file("decryption_error")
            return False
    
    def _backup_corrupted_file(self, reason: str):
        """
        Backup a corrupted token file for debugging.
        
        Args:
            reason (str): Reason for backup (e.g., "json_error", "decryption_error")
        """
        try:
            import shutil
            filepath_obj = Path(self._token_file_path)
            if filepath_obj.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = filepath_obj.with_suffix(f".corrupted.{reason}.{timestamp}")
                shutil.copy2(filepath_obj, backup_path)
                logger.info(f"Backed up corrupted token file to: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to backup corrupted file: {e}")
    
    def load_state(self) -> bool:
        """
        Load token state from encrypted file (call on bot startup).
        
        Returns:
            bool: True if state loaded successfully, False otherwise
        
        Example:
            >>> token_manager = TokenManager(enc, "data/tokens.enc", True)
            >>> if token_manager.load_state():
            ...     print("Token restored from previous session")
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping load_state")
            return False
        
        return self._load_from_disk()
    
    def save_state(self) -> bool:
        """
        Save token state to encrypted file (call on bot shutdown).
        
        Returns:
            bool: True if state saved successfully, False otherwise
        
        Example:
            >>> token_manager.save_state()  # Save before shutdown
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping save_state")
            return False
        
        return self._save_to_disk()
