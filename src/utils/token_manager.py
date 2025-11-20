"""
Token Manager Module

This module provides centralized multi-user token management for Microsoft Outlook
authentication. It stores and retrieves access tokens per Telegram user across bot 
sessions with optional encrypted persistence to disk.

Classes:
    TokenData: Container for user-specific token data
    TokenManager: Manages Microsoft Graph API access tokens with multi-user support

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
    
    # Set token for specific user
    user_id = update.effective_user.id
    token_manager.set_token(user_id, "eyJ0eXAiOiJKV1QiLCJub...")  # Auto-saves
    
    # Get token for specific user
    token = token_manager.get_token(user_id)
    
    token_manager.save_state()  # Explicit save on shutdown
"""

import logging
import json
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TokenData:
    """
    Container for user-specific token data.
    
    Attributes:
        access_token (str): Microsoft Graph API access token
        set_at (datetime): Timestamp when token was set
    """
    access_token: str
    set_at: datetime


class TokenManager:
    """
    Manages Microsoft Graph API access tokens with multi-user support and optional encrypted persistence.
    
    This class provides a centralized way to store and retrieve Outlook
    access tokens for multiple users. Supports both in-memory storage and encrypted 
    disk persistence for seamless bot restarts without re-authentication.
    
    Attributes:
        _tokens (Dict[int, TokenData]): Dictionary mapping user IDs to token data
        _persistence_enabled (bool): Whether to persist state to disk
        _encryption_manager (EncryptionManager or None): For token encryption
        _token_file_path (str): Path to encrypted token file
    
    Methods:
        set_token(user_id, token): Store an access token for a specific user (auto-saves if persistence enabled)
        get_token(user_id): Retrieve the stored token for a specific user
        clear_token(user_id): Remove the stored token for a specific user
        has_token(user_id): Check if a token is stored for a specific user
        get_token_age(user_id): Get the age of the stored token in seconds for a specific user
        get_token_info(user_id): Get information about the stored token for a specific user
        load_state(): Load tokens from encrypted file (call on startup)
        save_state(): Save tokens to encrypted file (call on shutdown)
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
        self._tokens: Dict[int, TokenData] = {}
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
    
    def set_token(self, user_id: int, token: str) -> None:
        """
        Store an access token for a specific user.
        
        This method saves the Microsoft Graph API access token obtained
        from the device code flow authentication. The token is stored
        with a timestamp for age tracking.
        
        Args:
            user_id (int): Telegram user ID
            token (str): Microsoft Graph API access token
                Example: "eyJ0eXAiOiJKV1QiLCJub..."
                
        Returns:
            None
            
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> token_manager.set_token(user_id, "eyJ0eXAiOiJKV1QiLCJub...")
            >>> print("Token stored successfully")
        """
        token_data = TokenData(access_token=token, set_at=datetime.now())
        self._tokens[user_id] = token_data
        logger.info(
            f"Access token stored for user {user_id} (length: {len(token)} chars, "
            f"set at: {token_data.set_at.isoformat()})"
        )
        
        # Auto-save if persistence is enabled
        if self._persistence_enabled:
            self._save_to_disk()
    
    def get_token(self, user_id: int) -> Optional[str]:
        """
        Retrieve the stored access token for a specific user.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            str or None: The stored access token if available, None otherwise
            
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> token = token_manager.get_token(user_id)
            >>> if token:
            ...     print("Using stored token")
            ... else:
            ...     print("No token available, need to authenticate")
        """
        token_data = self._tokens.get(user_id)
        if token_data:
            logger.debug(
                f"Retrieved access token for user {user_id} (length: {len(token_data.access_token)} chars)"
            )
            return token_data.access_token
        else:
            logger.debug(f"No access token available for user {user_id}")
            return None
    
    def clear_token(self, user_id: int) -> bool:
        """
        Remove the stored access token for a specific user.
        
        Useful when logging out or when a token expires/becomes invalid.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            bool: True if a token was cleared, False if no token was stored
            
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> was_cleared = token_manager.clear_token(user_id)
            >>> if was_cleared:
            ...     print("Token cleared")
        """
        token_data = self._tokens.get(user_id)
        if token_data:
            token_length = len(token_data.access_token)
            del self._tokens[user_id]
            logger.info(f"Access token cleared for user {user_id} (was {token_length} chars)")
            return True
        else:
            logger.debug(f"No token to clear for user {user_id}")
            return False
    
    def has_token(self, user_id: int) -> bool:
        """
        Check if an access token is stored for a specific user.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            bool: True if a token is stored, False otherwise
            
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> if not token_manager.has_token(user_id):
            ...     print("Please authenticate first")
        """
        return user_id in self._tokens
    
    def get_token_age(self, user_id: int) -> Optional[float]:
        """
        Get the age of the stored token in seconds for a specific user.
        
        Useful for implementing token refresh logic or warning users
        about expired tokens. Microsoft Graph tokens typically expire
        after 1 hour.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            float or None: Token age in seconds if token is stored,
                None if no token is available
            
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> age = token_manager.get_token_age(user_id)
            >>> if age and age > 3600:
            ...     print("Token may be expired (>1 hour old)")
        """
        token_data = self._tokens.get(user_id)
        if token_data is None:
            logger.debug(f"Cannot calculate token age for user {user_id} - no token stored")
            return None
        
        age_seconds = (datetime.now() - token_data.set_at).total_seconds()
        logger.debug(f"Token age for user {user_id}: {age_seconds:.2f} seconds")
        return age_seconds
    
    def get_token_info(self, user_id: int) -> dict:
        """
        Get information about the stored token for a specific user.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            dict: Dictionary containing:
                - has_token (bool): Whether a token is stored
                - token_length (int or None): Length of token string
                - token_age_seconds (float or None): Age in seconds
                - set_at (str or None): ISO format timestamp when set
                
        Example:
            >>> token_manager = TokenManager()
            >>> user_id = 123456789
            >>> info = token_manager.get_token_info(user_id)
            >>> print(f"Token info: {info}")
        """
        token_data = self._tokens.get(user_id)
        return {
            "has_token": self.has_token(user_id),
            "token_length": len(token_data.access_token) if token_data else None,
            "token_age_seconds": self.get_token_age(user_id),
            "set_at": token_data.set_at.isoformat() if token_data else None
        }
    
    def _save_to_disk(self) -> bool:
        """
        Save tokens to encrypted file (private method, called automatically).
        
        Returns:
            bool: True if save succeeded, False otherwise
        """
        if not self._persistence_enabled:
            return False
        
        if not self._tokens:
            logger.debug("No tokens to save")
            return False
        
        try:
            from .file_operations import rotate_backups
            
            # Prepare data to save in version 2.0 format
            tokens_dict = {}
            for user_id, token_data in self._tokens.items():
                tokens_dict[str(user_id)] = {
                    "access_token": token_data.access_token,
                    "set_at": token_data.set_at.isoformat()
                }
            
            data = {
                "version": "2.0",
                "tokens": tokens_dict,
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
            
            logger.info(f"Tokens saved to encrypted file: {self._token_file_path} ({len(self._tokens)} users)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tokens to disk: {e}", exc_info=True)
            return False
    
    def _load_from_disk(self) -> bool:
        """
        Load tokens from encrypted file (private method).
        Supports migration from version 1.0 (single-user) to version 2.0 (multi-user).
        
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
            
            version = data.get("version", "1.0")
            
            # Handle version 2.0 (multi-user format)
            if version == "2.0" and "tokens" in data:
                tokens_dict = data["tokens"]
                for user_id_str, token_info in tokens_dict.items():
                    user_id = int(user_id_str)
                    access_token = token_info["access_token"]
                    set_at_str = token_info["set_at"]
                    set_at = datetime.fromisoformat(set_at_str)
                    self._tokens[user_id] = TokenData(access_token=access_token, set_at=set_at)
                
                logger.info(
                    f"Tokens loaded from encrypted file: {self._token_file_path} "
                    f"({len(self._tokens)} users)"
                )
                return True
            
            # Handle version 1.0 (single-user format) - migrate to 2.0
            elif "access_token" in data:
                logger.info("Detected version 1.0 token file, migrating to version 2.0...")
                access_token = data["access_token"]
                token_set_at_str = data.get("token_set_at")
                
                if token_set_at_str:
                    set_at = datetime.fromisoformat(token_set_at_str)
                else:
                    set_at = datetime.now()
                
                # Use sentinel user ID -1 for legacy token
                sentinel_user_id = -1
                self._tokens[sentinel_user_id] = TokenData(access_token=access_token, set_at=set_at)
                
                # Save in new format
                self._save_to_disk()
                
                logger.info(
                    f"Migrated token file from single-user to multi-user format "
                    f"(legacy token stored with user_id={sentinel_user_id})"
                )
                return True
            
            else:
                logger.error(f"Unknown token file format: {data}")
                return False
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error loading tokens: {e}")
            self._backup_corrupted_file("json_error")
            return False
            
        except Exception as e:
            # Could be decryption error (wrong key, corrupted data)
            logger.error(f"Failed to load tokens from disk: {e}")
            if "InvalidToken" in str(type(e).__name__):
                logger.error(
                    "Decryption failed - wrong encryption key or corrupted file. "
                    "Tokens will need to be re-authenticated."
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
        Supports automatic migration from version 1.0 to version 2.0.
        
        Returns:
            bool: True if state loaded successfully, False otherwise
        
        Example:
            >>> token_manager = TokenManager(enc, "data/tokens.enc", True)
            >>> if token_manager.load_state():
            ...     print("Tokens restored from previous session")
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping load_state")
            return False
        
        return self._load_from_disk()
    
    def save_state(self) -> bool:
        """
        Save token state to encrypted file (call on bot shutdown).
        Saves all users' tokens in version 2.0 format.
        
        Returns:
            bool: True if state saved successfully, False otherwise
        
        Example:
            >>> token_manager.save_state()  # Save before shutdown
        """
        if not self._persistence_enabled:
            logger.debug("Persistence disabled, skipping save_state")
            return False
        
        return self._save_to_disk()
