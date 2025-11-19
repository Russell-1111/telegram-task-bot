# Implementation Tasks

## 1. Test Infrastructure Setup

- [x] 1.1 Create `tests/test_persistence.py` file with module docstring
- [x] 1.2 Add shared fixtures to `tests/conftest.py` (mock EncryptionManager, TokenManager, UserStateManager, file paths)
- [x] 1.3 Configure pytest markers for persistence tests (if needed)
- [x] 1.4 Verify pytest-mock is installed and working

## 2. EncryptionManager Tests

- [x] 2.1 Test successful encryption and decryption roundtrip
- [x] 2.2 Test `verify_key()` returns True for valid keys
- [x] 2.3 Test initialization with invalid base64 key raises ValueError
- [x] 2.4 Test decryption of corrupted token raises InvalidToken
- [x] 2.5 Test decryption with wrong key fails
- [x] 2.6 Test `generate_key()` produces valid Fernet keys
- [x] 2.7 Test `create_with_new_key()` creates working instance

## 3. File Operations Tests

- [x] 3.1 Mock pathlib.Path, os, shutil for all tests
- [x] 3.2 Test `atomic_write` writes to .tmp then calls replace()
- [x] 3.3 Test `atomic_write` cleans up .tmp file on OSError
- [x] 3.4 Test `rotate_backups` shifts files correctly (.1 -> .2, .2 -> .3)
- [x] 3.5 Test `rotate_backups` deletes oldest backup when retention exceeded
- [x] 3.6 Test `safe_json_load` returns None for missing file
- [x] 3.7 Test `safe_json_load` backs up corrupted file on JSONDecodeError
- [x] 3.8 Test `safe_json_save` serializes and calls atomic_write
- [x] 3.9 Test `set_secure_permissions` calls chmod 0600 on Unix
- [x] 3.10 Test `set_secure_permissions` calls icacls on Windows (or logs appropriately)

## 4. TokenManager Tests

- [x] 4.1 Mock EncryptionManager and file_operations for all tests
- [x] 4.2 Test `set_token` triggers `_save_to_disk` when persistence enabled
- [x] 4.3 Test `set_token` does NOT save when persistence disabled
- [x] 4.4 Test `load_state` reads, decrypts, and restores token
- [x] 4.5 Test `load_state` returns False for missing file (no crash)
- [x] 4.6 Test `load_state` backs up corrupted file and returns False
- [x] 4.7 Test `save_state` failure does not crash bot (logs error)
- [x] 4.8 Test token timestamp is preserved across save/load

## 5. UserStateManager Tests

- [x] 5.1 Mock file_operations for all tests
- [x] 5.2 Test `set_user_task` triggers `_save_to_disk` when persistence enabled
- [x] 5.3 Test `set_user_task` does NOT save when persistence disabled
- [x] 5.4 Test `load_state` repopulates internal dictionary from JSON
- [x] 5.5 Test `load_state` handles missing file gracefully
- [x] 5.6 Test `load_state` handles partial corruption (valid JSON, missing keys)
- [x] 5.7 Test `save_state` serializes internal dict to JSON
- [x] 5.8 Test permission denied during save logs error but doesn't crash

## 6. AutoSaveThread Tests

- [x] 6.1 Mock threading.Event, time.sleep, and Manager classes
- [x] 6.2 Test `run` loop checks for changes via hash comparison
- [x] 6.3 Test `save_state` is ONLY called when data changed (hash differs)
- [x] 6.4 Test `save_state` is SKIPPED when data unchanged (hash same)
- [x] 6.5 Test `stop()` sets event and joins thread
- [x] 6.6 Test exception during save keeps thread alive and logs error
- [x] 6.7 Test final save is performed after stop() is called
- [x] 6.8 Test change detection for token state (via _compute_token_hash)
- [x] 6.9 Test change detection for user state (via _compute_state_hash)

## 7. Integration & Edge Cases

- [x] 7.1 Test full lifecycle: init -> set token -> save -> load -> verify
- [x] 7.2 Test concurrent auto-save doesn't interfere with manual saves
- [x] 7.3 Test backup rotation with multiple save cycles
- [x] 7.4 Test encryption key mismatch scenario
- [x] 7.5 Test disk full simulation (OSError during write)
- [x] 7.6 Test file permissions validation

## 8. Validation & Documentation

- [x] 8.1 Run pytest with coverage: `pytest tests/test_persistence.py --cov=src/utils`
- [x] 8.2 Verify ≥90% coverage for encryption.py, file_operations.py, token_manager.py, state_manager.py, auto_save.py
- [x] 8.3 Ensure all tests pass without actual disk I/O
- [x] 8.4 Add docstrings to test classes and complex test methods
- [x] 8.5 Update IMPLEMENTATION-COMPLETE.md to reflect testing status

## 9. OpenSpec Compliance

- [x] 9.1 Run `openspec validate add-persistence-tests --strict`
- [x] 9.2 Fix any validation errors
- [x] 9.3 Ensure all spec scenarios have corresponding tests
