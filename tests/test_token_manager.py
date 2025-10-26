"""
Unit tests for TokenManager

Tests cover:
- Setting access token
- Getting access token
- Clearing access token
- Checking if token exists
- Getting token age
- Getting token info
"""
import pytest
from datetime import datetime
import time
from utils.token_manager import TokenManager


class TestTokenManager:
    """Test suite for TokenManager class"""
    
    def test_initialization(self):
        """Test that TokenManager initializes with no token"""
        manager = TokenManager()
        assert not manager.has_token()
        assert manager.get_token() is None
        assert manager.get_token_age() is None
    
    def test_set_token(self):
        """Test setting an access token"""
        manager = TokenManager()
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."
        
        manager.set_token(token)
        
        assert manager.has_token()
        assert manager.get_token() == token
    
    def test_get_token_when_not_set(self):
        """Test getting token when none is set"""
        manager = TokenManager()
        assert manager.get_token() is None
    
    def test_has_token(self):
        """Test checking if token exists"""
        manager = TokenManager()
        
        assert not manager.has_token()
        
        manager.set_token("test_token_123")
        
        assert manager.has_token()
    
    def test_clear_token(self):
        """Test clearing the access token"""
        manager = TokenManager()
        
        # Set a token
        manager.set_token("test_token_123")
        assert manager.has_token()
        
        # Clear it
        result = manager.clear_token()
        assert result is True
        assert not manager.has_token()
        assert manager.get_token() is None
    
    def test_clear_when_no_token(self):
        """Test clearing when no token is set"""
        manager = TokenManager()
        result = manager.clear_token()
        assert result is False
    
    def test_get_token_age(self):
        """Test getting token age in seconds"""
        manager = TokenManager()
        
        # No token set
        assert manager.get_token_age() is None
        
        # Set token and wait a bit
        manager.set_token("test_token_123")
        time.sleep(0.1)  # Wait 100ms
        
        age = manager.get_token_age()
        assert age is not None
        assert age >= 0.1  # Should be at least 100ms
        assert age < 1.0   # Should be less than 1 second
    
    def test_get_token_info(self):
        """Test getting comprehensive token information"""
        manager = TokenManager()
        
        # No token set
        info = manager.get_token_info()
        assert info['has_token'] is False
        assert info['token_length'] is None
        assert info['token_age_seconds'] is None
        assert info['set_at'] is None
        
        # Set token
        token = "test_token_with_some_length"
        manager.set_token(token)
        
        info = manager.get_token_info()
        assert info['has_token'] is True
        assert info['token_length'] == len(token)
        assert info['token_age_seconds'] is not None
        assert info['set_at'] is not None
        assert isinstance(info['set_at'], str)  # ISO format string
    
    def test_token_replacement(self):
        """Test replacing an existing token"""
        manager = TokenManager()
        
        # Set initial token
        manager.set_token("old_token_123")
        old_age = manager.get_token_age()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Replace with new token
        manager.set_token("new_token_456")
        
        # Should have new token and refreshed timestamp
        assert manager.get_token() == "new_token_456"
        new_age = manager.get_token_age()
        # New token should be younger (close to 0 seconds old)
        assert new_age < 0.05  # Less than 50ms old
    
    def test_token_age_increases(self):
        """Test that token age increases over time"""
        manager = TokenManager()
        manager.set_token("test_token")
        
        age1 = manager.get_token_age()
        time.sleep(0.2)  # Wait 200ms
        age2 = manager.get_token_age()
        
        assert age2 > age1
        assert (age2 - age1) >= 0.2  # Should be at least 200ms difference
    
    def test_global_design(self):
        """Test that TokenManager works as a global singleton pattern"""
        # This tests the design - single token for entire bot
        manager1 = TokenManager()
        manager2 = TokenManager()
        
        # These are separate instances
        manager1.set_token("token_123")
        
        # manager2 won't have the same token (they're separate instances)
        # This is expected behavior - each instance is independent
        assert not manager2.has_token()
        
        # In actual usage, we use a single instance (imported from handlers)
