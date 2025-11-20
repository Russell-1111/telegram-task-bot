# user-authentication Specification

## Purpose
Defines multi-user authentication, token isolation, and session management for the Telegram Task Bot. Ensures each Telegram user has an independent, isolated Microsoft Outlook authentication session.

## ADDED Requirements

### Requirement: Per-User Token Isolation
The system SHALL maintain isolated Microsoft Graph API access tokens for each Telegram user, preventing token overwrites and session conflicts.

#### Scenario: Multiple users authenticate independently
- **WHEN** User A (Telegram ID 123456) authenticates via `/connectoutlook`
- **AND** User B (Telegram ID 789012) authenticates via `/connectoutlook`
- **THEN** User A's access token SHALL remain valid and accessible
- **AND** User B's access token SHALL be stored independently
- **AND** subsequent API calls by User A SHALL use User A's token
- **AND** subsequent API calls by User B SHALL use User B's token

#### Scenario: User token retrieval by ID
- **WHEN** a handler requests a token for a specific Telegram user ID
- **THEN** the system SHALL return the access token associated with that user ID
- **AND** the token SHALL NOT be affected by other users' authentication status
- **AND** if no token exists for that user ID, the system SHALL return None

#### Scenario: User-specific token clearing
- **WHEN** User A logs out or clears their token
- **THEN** only User A's token SHALL be removed from storage
- **AND** all other users' tokens SHALL remain intact
- **AND** User A SHALL require re-authentication for subsequent API calls
- **AND** other users SHALL continue to function normally

### Requirement: User Identity Verification
The system SHALL derive user identity exclusively from Telegram context (`update.effective_user.id`) for all authentication operations.

#### Scenario: Extract user ID from Telegram update
- **WHEN** a command or message handler is invoked
- **THEN** the system SHALL extract `user_id = update.effective_user.id`
- **AND** the user ID SHALL be an integer provided by Telegram
- **AND** the user ID SHALL be passed to all TokenManager operations

#### Scenario: Prevent user impersonation
- **WHEN** a user attempts to access tasks or authenticate
- **THEN** the system SHALL use only the Telegram-provided user ID
- **AND** the system SHALL NOT accept user ID from message text or user input
- **AND** the system SHALL NOT allow users to specify arbitrary user IDs

### Requirement: Token Lifecycle Management
The system SHALL manage the complete lifecycle of per-user authentication tokens, including creation, storage, retrieval, expiration handling, and deletion.

#### Scenario: Token creation and storage
- **WHEN** a user successfully completes the device code flow authentication
- **THEN** the system SHALL create a TokenData object containing the access token and timestamp
- **AND** the TokenData object SHALL be stored in the TokenManager dictionary keyed by user ID
- **AND** the token SHALL be persisted to encrypted disk storage (if persistence enabled)
- **AND** the storage operation SHALL be logged with the user ID

#### Scenario: Token expiration detection
- **WHEN** a token is older than 1 hour (Microsoft Graph token lifetime)
- **THEN** the system SHALL detect the age using `get_token_age(user_id)`
- **AND** API calls using expired tokens SHALL fail with 401 Unauthorized
- **AND** the system SHALL prompt the user to re-authenticate via `/connectoutlook`
- **AND** the expired token SHALL remain in storage until replaced or cleared

#### Scenario: Token absence handling
- **WHEN** a user attempts an operation requiring authentication but has no stored token
- **THEN** the system SHALL return None from `get_token(user_id)`
- **AND** the handler SHALL send a message instructing the user to run `/connectoutlook`
- **AND** the operation SHALL NOT proceed with invalid or missing authentication

### Requirement: Multi-User Persistence
The system SHALL persist all users' tokens to encrypted storage and restore them across bot restarts, maintaining isolation.

#### Scenario: Save multi-user token dictionary
- **WHEN** any user's token is set or updated
- **THEN** the entire token dictionary SHALL be serialized to JSON
- **AND** the JSON structure SHALL map user IDs (as string keys) to TokenData objects
- **AND** the serialized data SHALL be encrypted using the encryption manager
- **AND** the encrypted data SHALL be written atomically to `data/tokens.enc`

#### Scenario: Load multi-user token dictionary on startup
- **WHEN** the bot starts and an encrypted token file exists
- **THEN** the system SHALL decrypt the file contents
- **AND** the system SHALL deserialize the JSON into a dictionary of user IDs to TokenData
- **AND** all users' tokens SHALL be loaded into the TokenManager
- **AND** each user SHALL be able to use their restored token without re-authentication

#### Scenario: Handle corrupted multi-user token file
- **WHEN** the bot attempts to load a multi-user token file but decryption or parsing fails
- **THEN** the system SHALL backup the corrupted file with a timestamp suffix
- **AND** the system SHALL initialize with an empty token dictionary
- **AND** the system SHALL log an error with details
- **AND** all users SHALL need to re-authenticate via `/connectoutlook`

### Requirement: Backward Compatibility Migration
The system SHALL automatically migrate existing single-user token files to multi-user format without manual intervention.

#### Scenario: Detect and migrate legacy single-token format
- **WHEN** the bot loads an encrypted token file in the old single-token format (version 1.0)
- **THEN** the system SHALL detect the format by checking for a root-level "access_token" key
- **AND** the system SHALL wrap the token in a multi-user dictionary with a sentinel user ID (-1)
- **AND** the system SHALL save the migrated data in the new format (version 2.0)
- **AND** the system SHALL log an INFO message indicating successful migration

#### Scenario: Load already-migrated multi-user format
- **WHEN** the bot loads an encrypted token file in the new multi-user format (version 2.0)
- **THEN** the system SHALL detect the format by checking for a "tokens" dictionary key
- **AND** the system SHALL load the tokens directly without migration
- **AND** all users SHALL have their tokens restored correctly

### Requirement: TokenManager API Multi-Tenancy Enforcement
The system SHALL enforce multi-tenancy in all public TokenManager methods by requiring a `user_id` argument.

#### Scenario: Set token with user ID
- **WHEN** `set_token(user_id: int, token: str)` is called
- **THEN** the system SHALL create a TokenData object with the token and current timestamp
- **AND** the TokenData object SHALL be stored in `_tokens[user_id]`
- **AND** the operation SHALL be logged with the user ID and token length
- **AND** the token SHALL be auto-saved to disk if persistence is enabled

#### Scenario: Get token with user ID
- **WHEN** `get_token(user_id: int)` is called
- **THEN** the system SHALL look up the user ID in the `_tokens` dictionary
- **AND** if a TokenData object exists, the system SHALL return the access_token string
- **AND** if no TokenData exists, the system SHALL return None
- **AND** the retrieval SHALL be logged at DEBUG level

#### Scenario: Check token existence with user ID
- **WHEN** `has_token(user_id: int)` is called
- **THEN** the system SHALL return True if the user ID exists in the `_tokens` dictionary
- **AND** the system SHALL return False if the user ID does not exist
- **AND** no exceptions SHALL be raised for non-existent user IDs

#### Scenario: Get token age with user ID
- **WHEN** `get_token_age(user_id: int)` is called
- **THEN** if a token exists for the user, the system SHALL calculate the age in seconds
- **AND** the age SHALL be computed as `(datetime.now() - TokenData.set_at).total_seconds()`
- **AND** if no token exists for the user, the system SHALL return None

#### Scenario: Clear token with user ID
- **WHEN** `clear_token(user_id: int)` is called
- **THEN** if a token exists for the user, the system SHALL delete the entry from `_tokens`
- **AND** the system SHALL return True if a token was cleared
- **AND** the system SHALL return False if no token existed
- **AND** the operation SHALL be logged with the user ID

### Requirement: Concurrent User Operations
The system SHALL support concurrent authentication and token operations by multiple users without race conditions or data corruption.

#### Scenario: Simultaneous authentication by multiple users
- **WHEN** User A and User B both run `/connectoutlook` at the same time
- **THEN** both device code flows SHALL execute independently
- **AND** both tokens SHALL be stored correctly in the TokenManager
- **AND** no token overwrites or race conditions SHALL occur
- **AND** both users SHALL receive success confirmation messages

#### Scenario: Concurrent token retrieval during task operations
- **WHEN** User A creates a task while User B retrieves tasks
- **THEN** both operations SHALL retrieve the correct per-user tokens
- **AND** no cross-user token contamination SHALL occur
- **AND** both operations SHALL complete successfully
- **AND** the TokenManager SHALL handle concurrent reads safely
