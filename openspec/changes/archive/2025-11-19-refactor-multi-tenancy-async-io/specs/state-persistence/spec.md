# state-persistence Specification Deltas

## MODIFIED Requirements

### Requirement: Encrypted Token Persistence
The system SHALL persist Microsoft Graph API access tokens for **multiple users** to encrypted storage across bot restarts, maintaining per-user isolation.

#### Scenario: Token saved after authentication
- **WHEN** a user successfully authenticates via device code flow
- **THEN** the user's access token SHALL be encrypted using Fernet symmetric encryption
- **AND** the token SHALL be added to the multi-user token dictionary keyed by Telegram user ID
- **AND** the encrypted multi-user dictionary SHALL be saved to `data/tokens.enc` with restricted file permissions (0600 on Unix, user-only ACL on Windows)
- **AND** the token metadata (user ID and set timestamp) SHALL be included in the saved data

#### Scenario: Multi-user tokens restored on bot startup
- **WHEN** the bot starts and an encrypted token file exists
- **THEN** the system SHALL decrypt the file using the encryption key from `STATE_ENCRYPTION_KEY` environment variable
- **AND** the decrypted data SHALL be parsed as a multi-user token dictionary (user ID -> TokenData)
- **AND** all users' tokens SHALL be loaded into `TokenManager._tokens`
- **AND** the token timestamps SHALL be restored for each user
- **AND** the bot SHALL continue normal operation with all users' restored tokens

#### Scenario: Decryption failure recovery
- **WHEN** the bot attempts to load a token file but decryption fails (wrong key, corrupted data, or tampered file)
- **THEN** the system SHALL log an error with details
- **AND** the system SHALL backup the corrupted file to `data/tokens.corrupted.decryption_error.{timestamp}`
- **AND** the system SHALL initialize with an empty token dictionary (all users require re-authentication)
- **AND** the system SHALL notify the operator via logs that re-authentication is needed

#### Scenario: Missing encryption key
- **WHEN** the bot starts and `STATE_ENCRYPTION_KEY` environment variable is not set
- **THEN** the system SHALL auto-generate a new Fernet key
- **AND** the system SHALL log a warning message with the generated key
- **AND** the system SHALL save the key to a local file `data/.encryption_key` (with 0600 permissions)
- **AND** the system SHALL use the generated key for encryption/decryption
- **AND** the system SHALL prompt the operator to securely back up the key

### Requirement: User State Persistence
The system SHALL persist user task context (last created task per user) to storage across bot restarts, maintaining per-user isolation.

#### Scenario: User state saved after task creation
- **WHEN** a user creates a task successfully
- **THEN** the task information (id, title, due_date, created_at) SHALL be saved to `data/user_state.json`
- **AND** the save operation SHALL use atomic file writes (write to `.tmp`, then rename)
- **AND** the state SHALL be stored in a per-user structure keyed by Telegram user ID
- **AND** existing user state for other users SHALL be preserved

#### Scenario: User state restored on bot startup
- **WHEN** the bot starts and a user state file exists
- **THEN** the system SHALL parse the JSON file
- **AND** the system SHALL load all user task contexts into `UserStateManager._user_tasks` (user ID -> task data)
- **AND** the bot SHALL continue normal operation with restored context for all users
- **AND** the "update due date" feature SHALL work for previously created tasks by the correct users

#### Scenario: User state file corruption recovery
- **WHEN** the bot attempts to load user state but JSON parsing fails
- **THEN** the system SHALL log an error with parse failure details
- **AND** the system SHALL backup the corrupted file to `data/user_state.corrupted.json_error.{timestamp}`
- **AND** the system SHALL initialize with empty user state
- **AND** the bot SHALL continue operation (all users can create new tasks)

#### Scenario: Missing user state file on first run
- **WHEN** the bot starts and no user state file exists
- **THEN** the system SHALL initialize with empty user state dictionary
- **AND** the system SHALL create the `data/` directory structure if it doesn't exist
- **AND** the system SHALL log an info message indicating first-run initialization
- **AND** the bot SHALL continue normal operation

## ADDED Requirements

### Requirement: Multi-User Token Storage Format
The system SHALL use a versioned JSON structure to store multiple users' tokens in a single encrypted file, enabling per-user token isolation.

#### Scenario: Serialize multi-user token dictionary
- **WHEN** the TokenManager saves state to disk
- **THEN** the data structure SHALL have version "2.0" to indicate multi-user format
- **AND** the structure SHALL contain a "tokens" key mapping user IDs (as strings) to token data objects
- **AND** each token data object SHALL contain "access_token" (string) and "set_at" (ISO timestamp)
- **AND** the structure SHALL include metadata (encrypted_at timestamp)

#### Scenario: Deserialize multi-user token dictionary
- **WHEN** the TokenManager loads state from disk
- **THEN** the system SHALL parse the "tokens" dictionary from the JSON
- **AND** each user ID key SHALL be converted from string to integer
- **AND** each token data object SHALL be converted to a TokenData dataclass instance
- **AND** the entire dictionary SHALL be loaded into `TokenManager._tokens`

### Requirement: Automated Token Format Migration
The system SHALL automatically detect and migrate legacy single-user token files to multi-user format on first load.

#### Scenario: Migrate version 1.0 to version 2.0
- **WHEN** the bot loads a token file with version "1.0" (single-user format)
- **THEN** the system SHALL detect the old format by checking for root-level "access_token" key
- **AND** the system SHALL wrap the token in a multi-user dictionary with sentinel user ID -1
- **AND** the system SHALL update the version to "2.0"
- **AND** the system SHALL save the migrated file immediately
- **AND** the system SHALL log an INFO message: "Migrated token file from single-user to multi-user format"

#### Scenario: Skip migration for already-migrated files
- **WHEN** the bot loads a token file with version "2.0" (multi-user format)
- **THEN** the system SHALL load the tokens directly without migration
- **AND** no file writes SHALL occur during load (migration not needed)

### Requirement: Concurrent Token Persistence
The system SHALL handle concurrent token updates from multiple users safely, ensuring no data loss or corruption.

#### Scenario: Multiple users authenticate concurrently
- **WHEN** two or more users authenticate and trigger token saves simultaneously
- **THEN** the atomic file write operation SHALL serialize writes
- **AND** all users' tokens SHALL be present in the final saved file
- **AND** no tokens SHALL be lost due to race conditions
- **AND** the file SHALL remain in a valid, parseable state

#### Scenario: Token save during auto-save thread
- **WHEN** a user's token is set while the auto-save thread is saving state
- **THEN** the in-memory token dictionary SHALL be updated immediately
- **AND** the next auto-save cycle SHALL include the new token
- **AND** no exceptions SHALL be raised
- **AND** the file SHALL remain consistent
