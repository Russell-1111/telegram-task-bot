# state-persistence Specification

## Purpose
TBD - created by archiving change add-persistent-state. Update Purpose after archive.
## Requirements
### Requirement: Encrypted Token Persistence
The system SHALL persist Microsoft Graph API access tokens to encrypted storage across bot restarts.

#### Scenario: Token saved after authentication
- **WHEN** user successfully authenticates via device code flow
- **THEN** the access token SHALL be encrypted using Fernet symmetric encryption
- **AND** the encrypted token SHALL be saved to `data/tokens.enc` with restricted file permissions (0600 on Unix, user-only ACL on Windows)
- **AND** the token metadata (set timestamp) SHALL be included in the saved data

#### Scenario: Token restored on bot startup
- **WHEN** the bot starts and an encrypted token file exists
- **THEN** the system SHALL decrypt the token using the encryption key from `STATE_ENCRYPTION_KEY` environment variable
- **AND** the decrypted token SHALL be loaded into `TokenManager._access_token`
- **AND** the token timestamp SHALL be restored to `TokenManager._token_set_at`
- **AND** the bot SHALL continue normal operation with the restored token

#### Scenario: Decryption failure recovery
- **WHEN** the bot attempts to load a token file but decryption fails (wrong key, corrupted data, or tampered file)
- **THEN** the system SHALL log an error with details
- **AND** the system SHALL backup the corrupted file to `data/backups/tokens.enc.corrupted.{timestamp}`
- **AND** the system SHALL initialize with no token (requiring re-authentication)
- **AND** the system SHALL notify the operator via logs that re-authentication is needed

#### Scenario: Missing encryption key
- **WHEN** the bot starts and `STATE_ENCRYPTION_KEY` environment variable is not set
- **THEN** the system SHALL auto-generate a new Fernet key
- **AND** the system SHALL log a warning message with the generated key
- **AND** the system SHALL save the key to a local file `data/.encryption_key` (with 0600 permissions)
- **AND** the system SHALL use the generated key for encryption/decryption
- **AND** the system SHALL prompt the operator to securely back up the key

### Requirement: User State Persistence
The system SHALL persist user task context (last created task per user) to storage across bot restarts.

#### Scenario: User state saved after task creation
- **WHEN** a user creates a task successfully
- **THEN** the task information (id, title, due_date, created_at) SHALL be saved to `data/user_state.json`
- **AND** the save operation SHALL use atomic file writes (write to `.tmp`, then rename)
- **AND** existing user state for other users SHALL be preserved

#### Scenario: User state restored on bot startup
- **WHEN** the bot starts and a user state file exists
- **THEN** the system SHALL parse the JSON file
- **AND** the system SHALL load all user task contexts into `UserStateManager._user_tasks`
- **AND** the bot SHALL continue normal operation with restored context
- **AND** the "update due date" feature SHALL work for previously created tasks

#### Scenario: User state file corruption recovery
- **WHEN** the bot attempts to load user state but JSON parsing fails
- **THEN** the system SHALL log an error with parse failure details
- **AND** the system SHALL backup the corrupted file to `data/backups/user_state.json.corrupted.{timestamp}`
- **AND** the system SHALL initialize with empty user state
- **AND** the bot SHALL continue operation (users can create new tasks)

#### Scenario: Missing user state file on first run
- **WHEN** the bot starts and no user state file exists
- **THEN** the system SHALL initialize with empty user state
- **AND** the system SHALL create the `data/` directory structure if it doesn't exist
- **AND** the system SHALL log an info message indicating first-run initialization
- **AND** the bot SHALL continue normal operation

### Requirement: Automatic State Backups
The system SHALL maintain automatic backups of state files to prevent data loss from corruption.

#### Scenario: Backup rotation on save
- **WHEN** the system saves a state file that already exists
- **THEN** the system SHALL rotate existing backups before overwriting
- **AND** `file.ext` SHALL be copied to `data/backups/file.ext.1`
- **AND** `file.ext.1` SHALL be moved to `file.ext.2`
- **AND** `file.ext.2` SHALL be moved to `file.ext.3`
- **AND** `file.ext.3` SHALL be deleted (oldest backup pruned)
- **AND** the new state SHALL be written to `file.ext`

#### Scenario: Backup retention limit
- **WHEN** the system maintains backups
- **THEN** the system SHALL keep a maximum of 3 backup copies by default
- **AND** the retention count SHALL be configurable via `BACKUP_RETENTION_COUNT` environment variable
- **AND** older backups SHALL be automatically pruned when the limit is exceeded

#### Scenario: Backup restoration by operator
- **WHEN** an operator manually restores a backup file (copies `file.ext.1` to `file.ext`)
- **THEN** the system SHALL load the restored state on next startup
- **AND** the system SHALL continue normal operation with the restored data

### Requirement: Atomic File Operations
The system SHALL use atomic file operations to prevent corruption from interrupted writes.

#### Scenario: Atomic save operation
- **WHEN** the system saves state to disk
- **THEN** the system SHALL write data to a temporary file (`.tmp` suffix)
- **AND** the system SHALL verify the write completed successfully
- **AND** the system SHALL atomically rename the temporary file to the target filename
- **AND** the rename operation SHALL be atomic at the filesystem level (replacing existing file)

#### Scenario: Save failure recovery
- **WHEN** a save operation fails (disk full, permissions error, interrupted write)
- **THEN** the system SHALL log an error with failure details
- **AND** the system SHALL leave the existing state file unchanged
- **AND** the system SHALL remove the incomplete temporary file
- **AND** the system SHALL continue operation (state remains in memory)
- **AND** the system SHALL retry the save operation on the next trigger

### Requirement: Graceful Shutdown Persistence
The system SHALL save all state before bot shutdown to ensure data durability.

#### Scenario: Normal shutdown save
- **WHEN** the bot receives a shutdown signal (SIGTERM, SIGINT, or graceful stop command)
- **THEN** the system SHALL save current token state to encrypted storage
- **AND** the system SHALL save current user state to JSON storage
- **AND** the system SHALL wait for save operations to complete before terminating
- **AND** the system SHALL log confirmation of successful state persistence

#### Scenario: Shutdown save timeout
- **WHEN** the bot is shutting down and save operations exceed 5 seconds
- **THEN** the system SHALL log a warning about incomplete saves
- **AND** the system SHALL terminate to respect shutdown timeout
- **AND** the system SHALL rely on periodic auto-saves for data recovery

### Requirement: Periodic Auto-Save
The system SHALL automatically save state at regular intervals to protect against crashes.

#### Scenario: Background auto-save thread
- **WHEN** the bot is running normally
- **THEN** a background thread SHALL trigger state saves every 5 minutes
- **AND** the auto-save interval SHALL be configurable via `AUTO_SAVE_INTERVAL_SECONDS` environment variable
- **AND** the auto-save SHALL be debounced (skip if no changes since last save)
- **AND** the auto-save SHALL not block message processing

#### Scenario: Auto-save change detection
- **WHEN** the auto-save timer triggers
- **THEN** the system SHALL check if token state has changed since last save
- **AND** the system SHALL check if user state has changed since last save
- **AND** the system SHALL skip saving unchanged data (optimization)
- **AND** the system SHALL log debug message for skipped saves

### Requirement: Configuration for Persistence Settings
The system SHALL support configuration of persistence behavior via environment variables.

#### Scenario: Configure encryption key
- **WHEN** the operator sets `STATE_ENCRYPTION_KEY` environment variable
- **THEN** the system SHALL use the provided key for token encryption/decryption
- **AND** the key SHALL be a valid 32-byte base64-encoded Fernet key
- **AND** invalid keys SHALL cause startup failure with clear error message

#### Scenario: Configure data directory
- **WHEN** the operator sets `DATA_DIR` environment variable
- **THEN** the system SHALL use the specified directory for all state files
- **AND** the system SHALL create the directory if it doesn't exist
- **AND** the system SHALL verify write permissions on startup
- **AND** permission failures SHALL cause startup failure with clear error message

#### Scenario: Disable persistence
- **WHEN** the operator sets `ENABLE_PERSISTENCE=false` environment variable
- **THEN** the system SHALL disable all file I/O operations
- **AND** the system SHALL operate in memory-only mode (current behavior)
- **AND** the system SHALL log a warning that persistence is disabled
- **AND** all existing persistence code paths SHALL be skipped

#### Scenario: Configure backup retention
- **WHEN** the operator sets `BACKUP_RETENTION_COUNT` environment variable to an integer
- **THEN** the system SHALL keep the specified number of backup files
- **AND** the minimum value SHALL be 1 (keep at least 1 backup)
- **AND** the maximum value SHALL be 10 (prevent excessive disk usage)
- **AND** invalid values SHALL log a warning and use default value 3

### Requirement: Security and File Permissions
The system SHALL enforce secure file permissions to protect sensitive data.

#### Scenario: Secure file creation
- **WHEN** the system creates a new state file
- **THEN** the file SHALL be created with restricted permissions (0600 on Unix, user-only ACL on Windows)
- **AND** the system SHALL verify permissions after creation
- **AND** permission setting failures SHALL log a warning

#### Scenario: Permission validation on startup
- **WHEN** the bot starts and state files exist
- **THEN** the system SHALL check file permissions
- **AND** the system SHALL log a warning if permissions are too permissive (world-readable or group-readable)
- **AND** the system SHALL suggest corrective action in the warning message
- **AND** the bot SHALL continue operation (warning only, not fatal)

#### Scenario: Encryption key file security
- **WHEN** the system auto-generates an encryption key and saves to `data/.encryption_key`
- **THEN** the file SHALL be created with 0600 permissions (owner read/write only)
- **AND** the system SHALL verify the file is not world-readable
- **AND** the system SHALL add the file to `.gitignore` recommendations

### Requirement: Error Handling and Logging
The system SHALL provide comprehensive error handling and logging for persistence operations.

#### Scenario: Detailed error logging
- **WHEN** any persistence operation fails
- **THEN** the system SHALL log the error with full context (operation, file path, error message)
- **AND** the log level SHALL be ERROR for failures affecting functionality
- **AND** the log level SHALL be WARNING for non-critical issues
- **AND** the log SHALL include guidance for operator action when applicable

#### Scenario: Success confirmation logging
- **WHEN** state is successfully saved or loaded
- **THEN** the system SHALL log an INFO message confirming the operation
- **AND** the log SHALL include the file path and data summary (e.g., "Loaded 5 user states")
- **AND** sensitive data (tokens, keys) SHALL be redacted or omitted from logs

#### Scenario: Debug tracing
- **WHEN** the log level is set to DEBUG
- **THEN** the system SHALL log detailed trace information for persistence operations
- **AND** the logs SHALL include timing information (save/load duration)
- **AND** the logs SHALL include file sizes and change detection results
- **AND** the logs SHALL help diagnose performance or reliability issues

### Requirement: Backward Compatibility
The system SHALL maintain backward compatibility with existing in-memory behavior.

#### Scenario: Persistence disabled fallback
- **WHEN** persistence is disabled or unavailable (configuration, permission errors, or missing dependencies)
- **THEN** the system SHALL fall back to in-memory storage
- **AND** all existing functionality SHALL continue to work (authentication, task creation, updates)
- **AND** the system SHALL log a message indicating fallback mode
- **AND** users SHALL experience no feature degradation (only loss of persistence)

#### Scenario: Existing code compatibility
- **WHEN** existing code calls `TokenManager.set_token()` or `UserStateManager.set_user_task()`
- **THEN** the methods SHALL continue to work without code changes
- **AND** persistence SHALL be transparent (automatic save in background)
- **AND** method signatures SHALL remain unchanged
- **AND** return values SHALL remain unchanged

#### Scenario: Migration from in-memory
- **WHEN** the bot is upgraded from a non-persistent version to a persistent version
- **THEN** users with active sessions SHALL need to re-authenticate once (no existing state to restore)
- **AND** subsequent restarts SHALL restore state correctly
- **AND** no manual migration steps SHALL be required
- **AND** the upgrade SHALL be seamless after initial re-authentication

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

