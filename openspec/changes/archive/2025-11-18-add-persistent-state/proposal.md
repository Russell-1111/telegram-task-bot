# Proposal: Add Persistent State Management

## Why

The current `telegram-task-bot` implementation stores all critical user data in volatile in-memory dictionaries (`TokenManager._access_token` and `UserStateManager._user_tasks`). This causes two major problems:

1. **Authentication Loss**: Every bot restart forces all users to re-authenticate with Microsoft Outlook via the device code flow, creating friction and poor user experience
2. **Broken Context Memory**: The "update due date" feature relies on `UserStateManager` remembering the user's last created task, but this context is lost on restart, breaking a core feature

Users expect their authenticated session and task context to persist across bot restarts (updates, crashes, server maintenance), similar to how web applications maintain sessions.

## What Changes

Add secure file-based persistence for authentication tokens and user state:

- **Encrypted Token Storage**: Store Microsoft Graph API access tokens in an encrypted JSON file with proper file permissions
- **User State Persistence**: Save user task context (last created task per user) to disk with automatic serialization/deserialization
- **Automatic State Restoration**: Load saved state on bot startup, seamlessly resuming user sessions
- **Graceful Degradation**: Handle missing/corrupted state files with proper error handling and user notifications
- **Security-First Design**: Encrypt sensitive tokens using Fernet (symmetric encryption), store encryption key in environment variable separate from data
- **Backward Compatibility**: Existing in-memory behavior continues to work; persistence is additive with graceful fallback

**Breaking Changes**: None. This is an enhancement with backward compatibility. If persistence fails, the system degrades to current in-memory behavior.

## Impact

**Affected Specs**:
- New capability: `state-persistence` (ADDED)

**Affected Code**:
- `src/utils/token_manager.py` - Add file I/O and encryption methods
- `src/utils/state_manager.py` - Add persistence layer for user task state
- `src/bot.py` - Initialize persistence on startup, save on shutdown
- `requirements.txt` - Add `cryptography` package for Fernet encryption
- `config/settings.py` - Add configuration for persistence file paths and encryption key

**User-Visible Impact**:
- ✅ Users no longer need to re-authenticate after bot restarts
- ✅ "Update due date" feature works reliably across sessions
- ✅ Improved reliability and user experience
- ⚠️ New environment variable required: `STATE_ENCRYPTION_KEY` (bot will generate if missing)

**Security Impact**:
- ✅ Tokens encrypted at rest using industry-standard Fernet (symmetric encryption)
- ✅ File permissions restricted (0600 on Unix, appropriate ACLs on Windows)
- ✅ Encryption key stored separately from encrypted data
- ⚠️ Operators must secure `STATE_ENCRYPTION_KEY` environment variable
- ⚠️ Documentation needed for proper key management and rotation
