"""
Token Manager Module

This module provides centralized token management for Microsoft Outlook
authentication. It stores and retrieves access tokens across bot sessions.

Classes:
    TokenManager: Manages Microsoft Graph API access tokens

Usage:
    token_manager = TokenManager()
    token_manager.set_token("eyJ0eXAiOiJKV1QiLCJub...")
    token = token_manager.get_token()
    if token_manager.has_token():
        print("Token available")
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages Microsoft Graph API access tokens.
    
    This class provides a centralized way to store and retrieve Outlook
    access tokens. Currently supports a single token for the bot instance.
    Future enhancement: Support per-user tokens for multi-user scenarios.
    
    Attributes:
        _access_token (str or None): The stored access token
        _token_set_at (datetime or None): Timestamp when token was set
    
    Methods:
        set_token(): Store an access token
        get_token(): Retrieve the stored token
        clear_token(): Remove the stored token
        has_token(): Check if a token is stored
        get_token_age(): Get the age of the stored token in seconds
    """
    
    def __init__(self):
        """
        Initialize the TokenManager.
        
        Creates a manager with no token stored initially.
        """
        self._access_token: Optional[str] = None
        self._token_set_at: Optional[datetime] = None
        logger.info("TokenManager initialized")
    
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
