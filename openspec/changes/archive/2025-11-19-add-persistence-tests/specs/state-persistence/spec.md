# state-persistence Specification Deltas

## ADDED Requirements

### Requirement: Automated Test Suite for Encryption Manager
The system SHALL provide comprehensive unit tests for the EncryptionManager module to verify secure token encryption and error handling.

#### Scenario: Encryption and decryption roundtrip
- **WHEN** a plaintext token is encrypted and then decrypted
- **THEN** the decrypted value SHALL match the original plaintext exactly
- **AND** the intermediate ciphertext SHALL be in bytes format
- **AND** the ciphertext SHALL be base64-encoded Fernet format

#### Scenario: Key validation
- **WHEN** `verify_key()` is called with a valid encryption key
- **THEN** the method SHALL return True
- **AND** a test encryption/decryption cycle SHALL succeed

#### Scenario: Invalid key initialization
- **WHEN** EncryptionManager is initialized with an invalid base64 key
- **THEN** a ValueError SHALL be raised
- **AND** the error message SHALL explain that a valid Fernet key is required

#### Scenario: Corrupted token decryption
- **WHEN** decryption is attempted on corrupted ciphertext
- **THEN** an InvalidToken exception SHALL be raised
- **AND** the error SHALL be logged with details about corruption

#### Scenario: Wrong key decryption
- **WHEN** decryption is attempted with a different key than used for encryption
- **THEN** an InvalidToken exception SHALL be raised
- **AND** data integrity SHALL be protected (HMAC verification failure)

#### Scenario: Key generation
- **WHEN** `generate_key()` is called
- **THEN** a new valid Fernet key SHALL be generated
- **AND** the key SHALL be base64-encoded
- **AND** the key SHALL be 32 bytes when decoded

### Requirement: Automated Test Suite for File Operations
The system SHALL provide comprehensive unit tests for file operation utilities, mocking all disk I/O to prevent actual file writes during tests.

#### Scenario: Atomic write with temp file
- **WHEN** `atomic_write()` is called
- **THEN** the system SHALL write content to a file with .tmp suffix
- **AND** the system SHALL call `Path.replace()` to atomically rename the temp file
- **AND** no actual disk I/O SHALL occur (all operations mocked)

#### Scenario: Atomic write failure cleanup
- **WHEN** `atomic_write()` encounters an OSError during write
- **THEN** the system SHALL attempt to unlink (delete) the incomplete .tmp file
- **AND** the exception SHALL be propagated to the caller
- **AND** the original file SHALL remain unchanged

#### Scenario: Backup rotation with retention
- **WHEN** `rotate_backups()` is called with retention=3
- **THEN** file.ext.1 SHALL be moved to file.ext.2
- **AND** file.ext.2 SHALL be moved to file.ext.3
- **AND** file.ext.3 SHALL be deleted (oldest backup pruned)
- **AND** the current file.ext SHALL be copied to file.ext.1

#### Scenario: JSON parse error with backup
- **WHEN** `safe_json_load()` encounters a JSONDecodeError
- **THEN** the corrupted file SHALL be backed up with timestamp suffix
- **AND** the method SHALL return None
- **AND** the error SHALL be logged with line and column numbers

#### Scenario: Missing file returns None
- **WHEN** `safe_json_load()` is called on a non-existent file
- **THEN** the method SHALL return None
- **AND** no exception SHALL be raised
- **AND** a debug log SHALL indicate the file doesn't exist

#### Scenario: Secure permissions on Unix
- **WHEN** `set_secure_permissions()` is called on Unix/Linux systems
- **THEN** `os.chmod()` SHALL be called with mode 0o600
- **AND** the file SHALL be owner read/write only
- **AND** the operation SHALL be logged at debug level

#### Scenario: Secure permissions on Windows
- **WHEN** `set_secure_permissions()` is called on Windows
- **THEN** `icacls` SHALL be invoked to set user-only ACL (or logged if not available)
- **AND** permissions SHALL restrict access to current user
- **AND** fallback to basic chmod SHALL occur if icacls fails

### Requirement: Automated Test Suite for Token Manager
The system SHALL provide comprehensive unit tests for TokenManager persistence functionality, mocking encryption and file operations.

#### Scenario: Auto-save on token set
- **WHEN** `set_token()` is called with persistence_enabled=True
- **THEN** `_save_to_disk()` SHALL be invoked automatically
- **AND** the token SHALL be encrypted before saving
- **AND** the save operation SHALL be logged

#### Scenario: No save when persistence disabled
- **WHEN** `set_token()` is called with persistence_enabled=False
- **THEN** `_save_to_disk()` SHALL NOT be invoked
- **AND** the token SHALL only be stored in memory

#### Scenario: Load state from encrypted file
- **WHEN** `load_state()` is called with an existing encrypted token file
- **THEN** the file SHALL be read and decrypted
- **AND** `_access_token` SHALL be populated with the decrypted token
- **AND** `_token_set_at` timestamp SHALL be restored

#### Scenario: Load state with missing file
- **WHEN** `load_state()` is called but no token file exists
- **THEN** the method SHALL return False
- **AND** no exception SHALL be raised
- **AND** the manager SHALL initialize with no token

#### Scenario: Load state with corrupted file
- **WHEN** `load_state()` encounters a decryption error
- **THEN** the corrupted file SHALL be backed up
- **AND** the method SHALL return False
- **AND** the error SHALL be logged with details

#### Scenario: Save state failure does not crash
- **WHEN** `save_state()` encounters a write error
- **THEN** the error SHALL be logged
- **AND** the bot SHALL continue running
- **AND** the token SHALL remain in memory

#### Scenario: Token timestamp preservation
- **WHEN** a token is saved and then loaded
- **THEN** the `_token_set_at` timestamp SHALL be preserved exactly
- **AND** the timestamp SHALL be in ISO 8601 format

### Requirement: Automated Test Suite for User State Manager
The system SHALL provide comprehensive unit tests for UserStateManager persistence functionality, mocking file operations.

#### Scenario: Auto-save on user task set
- **WHEN** `set_user_task()` is called with persistence_enabled=True
- **THEN** `_save_to_disk()` SHALL be invoked automatically
- **AND** the internal dictionary SHALL be serialized to JSON
- **AND** the save operation SHALL be logged

#### Scenario: No save when persistence disabled
- **WHEN** `set_user_task()` is called with persistence_enabled=False
- **THEN** `_save_to_disk()` SHALL NOT be invoked
- **AND** the state SHALL only be stored in memory

#### Scenario: Load state from JSON file
- **WHEN** `load_state()` is called with an existing state file
- **THEN** the JSON SHALL be parsed
- **AND** `_user_tasks` dictionary SHALL be repopulated with all user data

#### Scenario: Load state with missing file
- **WHEN** `load_state()` is called but no state file exists
- **THEN** the method SHALL return False
- **AND** `_user_tasks` SHALL remain as empty dict
- **AND** no exception SHALL be raised

#### Scenario: Load state with partial corruption
- **WHEN** `load_state()` encounters valid JSON but missing required keys (e.g., "id" missing)
- **THEN** the method SHALL handle the missing keys gracefully
- **AND** partial data SHALL be loaded where possible
- **AND** a warning SHALL be logged about data inconsistency

#### Scenario: Permission denied during save
- **WHEN** `save_state()` encounters a PermissionError
- **THEN** the error SHALL be logged with details
- **AND** the bot SHALL continue running
- **AND** the state SHALL remain in memory

### Requirement: Automated Test Suite for Auto-Save Thread
The system SHALL provide comprehensive unit tests for AutoSaveThread functionality, mocking threading primitives and manager classes.

#### Scenario: Change detection for saves
- **WHEN** the auto-save timer triggers
- **THEN** the thread SHALL compute hashes of current token and user state
- **AND** the hashes SHALL be compared with `_last_token_hash` and `_last_state_hash`
- **AND** saves SHALL only occur if hashes differ (change detected)

#### Scenario: Skip save when unchanged
- **WHEN** the auto-save timer triggers and state is unchanged
- **THEN** `save_state()` SHALL NOT be called on managers
- **AND** a debug log SHALL indicate "unchanged, skipped"
- **AND** the thread SHALL continue running without errors

#### Scenario: Graceful shutdown
- **WHEN** `stop()` is called on the auto-save thread
- **THEN** `_stop_event.set()` SHALL be invoked
- **AND** the thread SHALL exit the main loop
- **AND** a final save SHALL be performed before thread termination
- **AND** `join(timeout=5)` SHALL be called to wait for thread

#### Scenario: Exception during save keeps thread alive
- **WHEN** an exception occurs during `_perform_save()`
- **THEN** the exception SHALL be caught and logged
- **AND** the thread SHALL continue running (not crash)
- **AND** the next save cycle SHALL proceed normally

#### Scenario: Token hash computation
- **WHEN** `_compute_token_hash()` is called
- **THEN** the current token SHALL be retrieved from TokenManager
- **AND** a SHA256 hash SHALL be computed from the token string
- **AND** the hash SHALL be returned as a hex string

#### Scenario: State hash computation
- **WHEN** `_compute_state_hash()` is called
- **THEN** the `_user_tasks` dictionary SHALL be serialized to JSON
- **AND** a SHA256 hash SHALL be computed from the JSON string
- **AND** keys SHALL be sorted for consistent ordering

#### Scenario: Get status information
- **WHEN** `get_status()` is called
- **THEN** a dictionary SHALL be returned with thread status
- **AND** the dict SHALL include `is_alive`, `interval_seconds`, `last_token_hash`, `last_state_hash`

### Requirement: Test Coverage Metrics
The system SHALL achieve and maintain high test coverage for persistence modules to ensure code quality and reliability.

#### Scenario: Coverage threshold enforcement
- **WHEN** tests are run with coverage reporting
- **THEN** coverage for `src/utils/encryption.py` SHALL be ≥90%
- **AND** coverage for `src/utils/file_operations.py` SHALL be ≥90%
- **AND** coverage for `src/utils/token_manager.py` (persistence methods) SHALL be ≥90%
- **AND** coverage for `src/utils/state_manager.py` (persistence methods) SHALL be ≥90%
- **AND** coverage for `src/utils/auto_save.py` SHALL be ≥90%

#### Scenario: No disk I/O during tests
- **WHEN** any persistence test is executed
- **THEN** all file operations SHALL be mocked
- **AND** no files SHALL be created in the real `data/` directory
- **AND** all path operations SHALL use mocked Path objects
- **AND** tests SHALL run in isolation without side effects

#### Scenario: Integration with existing test suite
- **WHEN** the new persistence tests are added
- **THEN** all existing 73 tests SHALL continue to pass
- **AND** no regressions SHALL be introduced
- **AND** the new tests SHALL integrate with existing pytest configuration
- **AND** coverage reports SHALL include persistence modules
