"""
Unit tests for TokenManager

Tests cover:
- Setting access token (multi-user)
- Getting access token (multi-user)
- Clearing access token (multi-user)
- Checking if token exists (multi-user)
- Getting token age (multi-user)
- Getting token info (multi-user)
- Multi-user token isolation
- Migration from version 1.0 to 2.0
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
        user_id = 123456789
        assert not manager.has_token(user_id)
        assert manager.get_token(user_id) is None
        assert manager.get_token_age(user_id) is None
    
    def test_set_token(self):
        """Test setting an access token for a user"""
        manager = TokenManager()
        user_id = 123456789
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."
        
        manager.set_token(user_id, token)
        
        assert manager.has_token(user_id)
        assert manager.get_token(user_id) == token
    
    def test_get_token_when_not_set(self):
        """Test getting token when none is set for a user"""
        manager = TokenManager()
        user_id = 123456789
        assert manager.get_token(user_id) is None
    
    def test_has_token(self):
        """Test checking if token exists for a user"""
        manager = TokenManager()
        user_id = 123456789
        
        assert not manager.has_token(user_id)
        
        manager.set_token(user_id, "test_token_123")
        
        assert manager.has_token(user_id)
    
    def test_clear_token(self):
        """Test clearing the access token for a user"""
        manager = TokenManager()
        user_id = 123456789
        
        # Set a token
        manager.set_token(user_id, "test_token_123")
        assert manager.has_token(user_id)
        
        # Clear it
        result = manager.clear_token(user_id)
        assert result is True
        assert not manager.has_token(user_id)
        assert manager.get_token(user_id) is None
    
    def test_clear_when_no_token(self):
        """Test clearing when no token is set for a user"""
        manager = TokenManager()
        user_id = 123456789
        result = manager.clear_token(user_id)
        assert result is False
    
    def test_get_token_age(self):
        """Test getting token age in seconds for a user"""
        manager = TokenManager()
        user_id = 123456789
        
        # No token set
        assert manager.get_token_age(user_id) is None
        
        # Set token and wait a bit
        manager.set_token(user_id, "test_token_123")
        time.sleep(0.1)  # Wait 100ms
        
        age = manager.get_token_age(user_id)
        assert age is not None
        assert age >= 0.1  # Should be at least 100ms
        assert age < 1.0   # Should be less than 1 second
    
    def test_get_token_info(self):
        """Test getting comprehensive token information for a user"""
        manager = TokenManager()
        user_id = 123456789
        
        # No token set
        info = manager.get_token_info(user_id)
        assert info['has_token'] is False
        assert info['token_length'] is None
        assert info['token_age_seconds'] is None
        assert info['set_at'] is None
        
        # Set token
        token = "test_token_with_some_length"
        manager.set_token(user_id, token)
        
        info = manager.get_token_info(user_id)
        assert info['has_token'] is True
        assert info['token_length'] == len(token)
        assert info['token_age_seconds'] is not None
        assert info['set_at'] is not None
        assert isinstance(info['set_at'], str)  # ISO format string
    
    def test_token_replacement(self):
        """Test replacing an existing token for a user"""
        manager = TokenManager()
        user_id = 123456789
        
        # Set initial token
        manager.set_token(user_id, "old_token_123")
        old_age = manager.get_token_age(user_id)
        
        # Wait a bit
        time.sleep(0.1)
        
        # Replace with new token
        manager.set_token(user_id, "new_token_456")
        
        # Should have new token and refreshed timestamp
        assert manager.get_token(user_id) == "new_token_456"
        new_age = manager.get_token_age(user_id)
        # New token should be younger (close to 0 seconds old)
        assert new_age < 0.05  # Less than 50ms old
    
    def test_token_age_increases(self):
        """Test that token age increases over time for a user"""
        manager = TokenManager()
        user_id = 123456789
        manager.set_token(user_id, "test_token")
        
        age1 = manager.get_token_age(user_id)
        time.sleep(0.2)  # Wait 200ms
        age2 = manager.get_token_age(user_id)
        
        assert age2 > age1
        assert (age2 - age1) >= 0.2  # Should be at least 200ms difference
    
    def test_multi_user_isolation(self):
        """Test that multiple users' tokens are stored independently"""
        manager = TokenManager()
        user_a = 111111111
        user_b = 222222222
        
        # Set tokens for both users
        manager.set_token(user_a, "token_user_a")
        manager.set_token(user_b, "token_user_b")
        
        # Verify both tokens are stored independently
        assert manager.has_token(user_a)
        assert manager.has_token(user_b)
        assert manager.get_token(user_a) == "token_user_a"
        assert manager.get_token(user_b) == "token_user_b"
        
        # Clear one user's token, should not affect the other
        manager.clear_token(user_a)
        assert not manager.has_token(user_a)
        assert manager.has_token(user_b)
        assert manager.get_token(user_b) == "token_user_b"
    
    def test_multi_user_token_replacement(self):
        """Test that replacing one user's token doesn't affect other users"""
        manager = TokenManager()
        user_a = 111111111
        user_b = 222222222
        
        # Set initial tokens
        manager.set_token(user_a, "token_a_v1")
        manager.set_token(user_b, "token_b_v1")
        
        # Replace user A's token
        manager.set_token(user_a, "token_a_v2")
        
        # User A has new token, User B unchanged
        assert manager.get_token(user_a) == "token_a_v2"
        assert manager.get_token(user_b) == "token_b_v1"
    
    def test_multiple_users_token_age(self):
        """Test that token ages are tracked independently per user"""
        manager = TokenManager()
        user_a = 111111111
        user_b = 222222222
        
        # Set token for user A
        manager.set_token(user_a, "token_a")
        time.sleep(0.2)  # Wait 200ms
        
        # Set token for user B
        manager.set_token(user_b, "token_b")
        
        # User A's token should be older than User B's
        age_a = manager.get_token_age(user_a)
        age_b = manager.get_token_age(user_b)
        
        assert age_a > age_b
        assert age_a >= 0.2  # At least 200ms old


class TestTokenManagerMigration:
    """Test suite for TokenManager version 1.0 to 2.0 migration"""
    
    def test_migration_from_v1_to_v2(self):
        """Test automatic migration from version 1.0 (single-token) to version 2.0 (multi-user)"""
        import tempfile
        import os
        import json
        from utils.encryption import EncryptionManager
        from cryptography.fernet import Fernet
        
        # Create a temporary file with version 1.0 format
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.enc') as f:
            temp_file = f.name
        
        try:
            # Generate encryption key for test
            test_key = Fernet.generate_key().decode()
            
            # Simulate version 1.0 data structure
            v1_data = {
                "version": "1.0",
                "access_token": "legacy_token_123",
                "token_set_at": datetime.now().isoformat(),
                "metadata": {
                    "encrypted_at": datetime.now().isoformat()
                }
            }
            
            # Encrypt and write to file using EncryptionManager
            encryption_manager = EncryptionManager(test_key)
            encrypted_content = encryption_manager.encrypt(json.dumps(v1_data))
            with open(temp_file, 'wb') as f:
                f.write(encrypted_content)
            
            # Load with TokenManager (should trigger migration)
            manager = TokenManager(
                token_file_path=temp_file,
                encryption_manager=encryption_manager,
                persistence_enabled=True
            )
            manager.load_state()
            
            # Verify migration: legacy token should be accessible with sentinel user_id=-1
            assert manager.has_token(-1)
            assert manager.get_token(-1) == "legacy_token_123"
            
            # Verify new users can be added
            manager.set_token(123456789, "new_user_token")
            assert manager.has_token(123456789)
            assert manager.get_token(123456789) == "new_user_token"
            
            # Legacy token should still exist
            assert manager.has_token(-1)
            
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_v2_format_loads_correctly(self):
        """Test that version 2.0 format loads without migration"""
        import tempfile
        import os
        import json
        from utils.encryption import EncryptionManager
        from cryptography.fernet import Fernet
        
        # Create a temporary file with version 2.0 format
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.enc') as f:
            temp_file = f.name
        
        try:
            # Generate encryption key for test
            test_key = Fernet.generate_key().decode()
            
            # Version 2.0 data structure
            v2_data = {
                "version": "2.0",
                "tokens": {
                    "111111111": {
                        "access_token": "user_a_token",
                        "set_at": datetime.now().isoformat()
                    },
                    "222222222": {
                        "access_token": "user_b_token",
                        "set_at": datetime.now().isoformat()
                    }
                },
                "metadata": {
                    "encrypted_at": datetime.now().isoformat()
                }
            }
            
            # Encrypt and write to file using EncryptionManager
            encryption_manager = EncryptionManager(test_key)
            encrypted_content = encryption_manager.encrypt(json.dumps(v2_data))
            with open(temp_file, 'wb') as f:
                f.write(encrypted_content)
            
            # Load with TokenManager
            manager = TokenManager(
                token_file_path=temp_file,
                encryption_manager=encryption_manager,
                persistence_enabled=True
            )
            manager.load_state()
            
            # Verify both users' tokens loaded correctly
            assert manager.has_token(111111111)
            assert manager.get_token(111111111) == "user_a_token"
            assert manager.has_token(222222222)
            assert manager.get_token(222222222) == "user_b_token"
            
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
