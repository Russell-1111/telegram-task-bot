# Implementation Tasks

## 1. Setup and Dependencies

- [x] 1.1 Add `cryptography>=41.0.0` to `requirements.txt`
- [x] 1.2 Add `data/` directory to `.gitignore` to prevent committing state files
- [x] 1.3 Create `data/` directory structure in deployment setup scripts
- [x] 1.4 Document encryption key setup in README.md
- [x] 1.5 Add environment variable examples to `config_template.py`

## 2. Configuration Updates

- [x] 2.1 Add `STATE_ENCRYPTION_KEY` to `AppConfig` in `src/config/settings.py`
- [x] 2.2 Add `DATA_DIR` with default value `"data"` to `AppConfig`
- [x] 2.3 Add `ENABLE_PERSISTENCE` with default value `True` to `AppConfig`
- [x] 2.4 Add `BACKUP_RETENTION_COUNT` with default value `3` to `AppConfig`
- [x] 2.5 Add `AUTO_SAVE_INTERVAL_SECONDS` with default value `300` (5 minutes) to `AppConfig`
- [x] 2.6 Add validation for encryption key format (base64-encoded, 32 bytes when decoded)
- [x] 2.7 Add validation for data directory (exists or can be created, writable permissions)

## 3. Encryption Utilities Module

- [x] 3.1 Create `src/utils/encryption.py` module
- [x] 3.2 Implement `EncryptionManager` class with Fernet wrapper
- [x] 3.3 Add `generate_key() -> str` method to generate new Fernet keys
- [x] 3.4 Add `encrypt(plaintext: str) -> bytes` method
- [x] 3.5 Add `decrypt(ciphertext: bytes) -> str` method
- [x] 3.6 Add error handling for invalid keys and decryption failures
- [ ] 3.7 Add unit tests for encryption/decryption roundtrip
- [ ] 3.8 Add unit tests for invalid key handling
- [ ] 3.9 Add unit tests for corrupted ciphertext handling

## 4. File Operations Utilities Module

- [x] 4.1 Create `src/utils/file_operations.py` module
- [x] 4.2 Implement `atomic_write(filepath: str, content: str)` function (write to .tmp, then rename)
- [x] 4.3 Implement `set_secure_permissions(filepath: str)` function (0600 on Unix, user ACL on Windows)
- [x] 4.4 Implement `rotate_backups(filepath: str, retention: int)` function
- [x] 4.5 Implement `safe_json_load(filepath: str) -> dict` function with error handling
- [x] 4.6 Implement `safe_json_save(filepath: str, data: dict)` function with error handling
- [ ] 4.7 Add unit tests for atomic writes
- [ ] 4.8 Add unit tests for permission setting (platform-specific)
- [ ] 4.9 Add unit tests for backup rotation
- [ ] 4.10 Add unit tests for JSON error handling

## 5. TokenManager Persistence

- [x] 5.1 Add `_persistence_enabled: bool` attribute to `TokenManager.__init__()`
- [x] 5.2 Add `_encryption_manager: EncryptionManager` attribute to `TokenManager.__init__()`
- [x] 5.3 Add `_token_file_path: str` attribute to `TokenManager.__init__()` (from config)
- [x] 5.4 Implement `_save_to_disk()` private method in `TokenManager`
  - Serialize token data to JSON (token, timestamp, metadata)
  - Encrypt JSON string using `EncryptionManager`
  - Use `atomic_write()` to save encrypted bytes
  - Call `rotate_backups()` before writing
  - Handle errors gracefully (log but don't crash)
- [x] 5.5 Implement `_load_from_disk()` private method in `TokenManager`
  - Read encrypted bytes from file
  - Decrypt using `EncryptionManager`
  - Parse JSON and restore `_access_token` and `_token_set_at`
  - Handle missing file (normal on first run)
  - Handle decryption errors (backup corrupted file, start fresh)
  - Handle JSON parse errors (backup corrupted file, start fresh)
- [x] 5.6 Update `set_token()` to call `_save_to_disk()` after setting token (if persistence enabled)
- [x] 5.7 Add `load_state()` public method to trigger `_load_from_disk()` (called on bot startup)
- [x] 5.8 Add `save_state()` public method to trigger `_save_to_disk()` (called on bot shutdown)
- [ ] 5.9 Add unit tests for token save/load roundtrip
- [ ] 5.10 Add unit tests for encryption failure handling
- [ ] 5.11 Add unit tests for corrupted file recovery
- [ ] 5.12 Add unit tests for missing file initialization

## 6. UserStateManager Persistence

- [x] 6.1 Add `_persistence_enabled: bool` attribute to `UserStateManager.__init__()`
- [x] 6.2 Add `_state_file_path: str` attribute to `UserStateManager.__init__()` (from config)
- [x] 6.3 Implement `_save_to_disk()` private method in `UserStateManager`
  - Serialize `_user_tasks` to JSON (with version and metadata)
  - Use `safe_json_save()` with atomic writes
  - Call `rotate_backups()` before writing
  - Handle errors gracefully (log but don't crash)
- [x] 6.4 Implement `_load_from_disk()` private method in `UserStateManager`
  - Use `safe_json_load()` to read JSON file
  - Parse and restore `_user_tasks` dictionary
  - Handle missing file (normal on first run)
  - Handle JSON parse errors (backup corrupted file, start fresh)
- [x] 6.5 Update `set_user_task()` to call `_save_to_disk()` after setting state (if persistence enabled)
- [x] 6.6 Add `load_state()` public method to trigger `_load_from_disk()` (called on bot startup)
- [x] 6.7 Add `save_state()` public method to trigger `_save_to_disk()` (called on bot shutdown)
- [ ] 6.8 Add unit tests for user state save/load roundtrip
- [ ] 6.9 Add unit tests for multi-user state persistence
- [ ] 6.10 Add unit tests for corrupted file recovery
- [ ] 6.11 Add unit tests for missing file initialization

## 7. Bot Startup Integration

- [x] 7.1 Update `src/bot.py` to import `EncryptionManager`
- [x] 7.2 Initialize `EncryptionManager` with key from config (or auto-generate)
- [x] 7.3 Pass `EncryptionManager` to `TokenManager` and `UserStateManager` during initialization
- [x] 7.4 Call `token_manager.load_state()` before starting bot polling
- [x] 7.5 Call `state_manager.load_state()` before starting bot polling
- [x] 7.6 Add error handling for load failures (log and continue with empty state)
- [x] 7.7 Log info messages confirming state restored (token available, user count)
- [ ] 7.8 Add integration test: start bot, verify state loaded

## 8. Bot Shutdown Integration

- [x] 8.1 Add signal handlers for SIGTERM and SIGINT in `src/bot.py`
- [x] 8.2 Implement `graceful_shutdown()` function in `src/bot.py`
- [x] 8.3 Call `token_manager.save_state()` in shutdown handler
- [x] 8.4 Call `state_manager.save_state()` in shutdown handler
- [x] 8.5 Add timeout for shutdown saves (5 seconds max)
- [x] 8.6 Log confirmation of successful shutdown saves
- [ ] 8.7 Add integration test: stop bot, verify state saved

## 9. Periodic Auto-Save

- [x] 9.1 Create `src/utils/auto_save.py` module
- [x] 9.2 Implement `AutoSaveThread` class extending `threading.Thread`
- [x] 9.3 Add `__init__(token_manager, state_manager, interval_seconds)` constructor
- [x] 9.4 Implement `run()` method with periodic save loop
- [x] 9.5 Add change detection (track last save hash, skip if no changes)
- [x] 9.6 Add graceful stop mechanism (threading.Event for shutdown signal)
- [x] 9.7 Handle exceptions in auto-save loop (log but keep thread running)
- [x] 9.8 Initialize and start `AutoSaveThread` in `src/bot.py` (if persistence enabled)
- [x] 9.9 Stop `AutoSaveThread` in graceful shutdown handler
- [ ] 9.10 Add unit tests for auto-save thread lifecycle
- [ ] 9.11 Add unit tests for change detection optimization

## 10. Error Handling and Logging

- [x] 10.1 Add dedicated logger for persistence operations (`utils.persistence`)
- [x] 10.2 Ensure all file operations log errors with full context (operation, file, error)
- [x] 10.3 Ensure all encryption operations log errors without exposing keys
- [x] 10.4 Add INFO logs for successful save/load operations
- [x] 10.5 Add DEBUG logs for timing and performance metrics
- [x] 10.6 Add WARNING logs for permission issues and misconfigurations
- [x] 10.7 Ensure sensitive data (tokens, keys) is redacted from logs

## 11. Documentation

- [x] 11.1 Update README.md with persistence setup section
  - Explain encryption key generation and storage
  - Document required environment variables
  - Provide example `.env` file entries
- [x] 11.2 Create `docs/PERSISTENCE-GUIDE.md` with detailed setup instructions
  - Step-by-step encryption key setup
  - File permission requirements
  - Backup and restore procedures
  - Troubleshooting common errors
- [ ] 11.3 Update `docs/SETUP.md` with persistence configuration steps
- [x] 11.4 Add security section to README.md documenting:
  - Encryption at rest
  - Key management best practices
  - File permission requirements
  - What to include/exclude in backups
- [x] 11.5 Update `config_template.py` with persistence environment variable examples

## 12. Testing and Validation

- [ ] 12.1 Run all unit tests: `pytest tests/ -v`
- [ ] 12.2 Run tests with coverage: `pytest tests/ --cov=src --cov-report=html`
- [ ] 12.3 Verify coverage for new modules (target: >90%)
- [ ] 12.4 Manual test: Start bot, authenticate, restart bot, verify no re-auth needed
- [ ] 12.5 Manual test: Create task, restart bot, use "update due date", verify it works
- [ ] 12.6 Manual test: Corrupt `tokens.enc` file, restart bot, verify graceful recovery
- [ ] 12.7 Manual test: Delete encryption key, restart bot, verify auto-generation
- [ ] 12.8 Manual test: Set wrong encryption key, restart bot, verify error handling
- [ ] 12.9 Manual test: Verify file permissions (0600 on Unix, check with `ls -la data/`)
- [ ] 12.10 Test on Windows (target deployment platform)
- [ ] 12.11 Test graceful shutdown (Ctrl+C), verify state saved
- [ ] 12.12 Test periodic auto-save (wait 5+ minutes, check timestamps)

## 13. Deployment Preparation

- [ ] 13.1 Update `setup-env.ps1` to include persistence environment variables
- [ ] 13.2 Create `scripts/generate-encryption-key.py` utility script
- [ ] 13.3 Add `data/` directory creation to deployment checklist
- [ ] 13.4 Create operator checklist for secure deployment (key backup, permissions)
- [ ] 13.5 Test deployment from scratch on clean environment
- [ ] 13.6 Verify `.gitignore` prevents committing state files
- [ ] 13.7 Test backup/restore procedures manually

## 14. Backward Compatibility Validation

- [ ] 14.1 Test with `ENABLE_PERSISTENCE=false` (verify in-memory fallback)
- [ ] 14.2 Verify existing tests pass without modifications
- [ ] 14.3 Verify no breaking changes to `TokenManager` or `UserStateManager` public APIs
- [ ] 14.4 Test upgrade path: deploy to environment with existing users (expect one re-auth)

## Dependencies

**Task Dependencies** (must complete in order):
- Section 1-2 (Setup) → Section 3-4 (Utilities) → Section 5-6 (Manager Updates) → Section 7-9 (Integration)
- Section 3 (Encryption) is prerequisite for Section 5 (TokenManager)
- Section 4 (File Ops) is prerequisite for Section 5-6 (Both Managers)
- Section 7-8 (Bot Integration) requires Section 5-6 complete
- Section 12-14 (Testing) can start after Section 7 but requires all code complete

**Parallelizable Work**:
- Section 3 (Encryption Utils) and Section 4 (File Ops) can be done in parallel
- Section 5 (TokenManager) and Section 6 (UserStateManager) can be done in parallel after Section 3-4 complete
- Section 11 (Documentation) can be done in parallel with Section 12 (Testing)
