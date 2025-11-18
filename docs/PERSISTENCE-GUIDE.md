# 🔐 Persistent State Management Guide

This guide explains how to set up, configure, and troubleshoot the persistent state management feature in the Telegram Task Bot.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Security](#security)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

## 🎯 Overview

### What is Persistent State Management?

The bot now saves your authentication tokens and user state to disk, allowing you to:

- **Resume sessions** after bot restarts
- **Preserve authentication** without re-authenticating
- **Maintain task context** across restarts
- **Recover from crashes** with minimal data loss

### How It Works

1. **Encryption**: Microsoft Graph tokens are encrypted using Fernet (AES-128-CBC + HMAC)
2. **Auto-Save**: Background thread saves state every 5 minutes
3. **Atomic Writes**: Uses temp file + rename to prevent corruption
4. **Backups**: Keeps 3 rotating backups of each state file
5. **Graceful Shutdown**: Saves state on SIGTERM, SIGINT, and normal exit

### What Gets Saved?

- **Tokens** (`data/tokens.enc`): Encrypted Microsoft Graph access tokens
- **User State** (`data/user_state.json`): User task context (last task created, due dates)
- **Backups** (`data/backups/`): Rotating backups of both files

## 🚀 Quick Start

### Option 1: Auto-Generated Key (Simplest)

1. **Enable persistence** in `.env`:
   ```
   ENABLE_PERSISTENCE=true
   ```

2. **Start the bot**:
   ```powershell
   .\start-bot.bat
   ```

3. **Save the auto-generated key** (printed on first run):
   ```
   ============================================================
   AUTO-GENERATED ENCRYPTION KEY
   Key: dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlc3Q=
   IMPORTANT: Set STATE_ENCRYPTION_KEY environment variable
   to preserve this key across restarts!
   ============================================================
   ```

4. **Add key to `.env`** (to preserve across restarts):
   ```
   STATE_ENCRYPTION_KEY=dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlc3Q=
   ```

### Option 2: Manual Key Generation (Recommended)

1. **Generate a secure key**:
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   
   Output example: `vF3jH9kL2mP5qR8sT1uW4xY7zA0bC3dE6fG9hI2jK5m=`

2. **Add to `.env` file**:
   ```
   STATE_ENCRYPTION_KEY=vF3jH9kL2mP5qR8sT1uW4xY7zA0bC3dE6fG9hI2jK5m=
   ENABLE_PERSISTENCE=true
   DATA_DIR=data
   BACKUP_RETENTION_COUNT=3
   AUTO_SAVE_INTERVAL_SECONDS=300
   ```

3. **Start the bot**:
   ```powershell
   .\start-bot.bat
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `STATE_ENCRYPTION_KEY` | string | *(auto-generated)* | Base64-encoded 32-byte Fernet key |
| `ENABLE_PERSISTENCE` | boolean | `true` | Enable/disable persistence |
| `DATA_DIR` | string | `data` | Directory for state files |
| `BACKUP_RETENTION_COUNT` | integer | `3` | Number of backups to keep (1-10) |
| `AUTO_SAVE_INTERVAL_SECONDS` | integer | `300` | Auto-save interval in seconds (0 = disable) |

### Configuration Examples

#### Disable Persistence (In-Memory Only)
```bash
ENABLE_PERSISTENCE=false
```

#### Custom Data Directory
```bash
DATA_DIR=/var/lib/telegram-task-bot/state
```

#### More Frequent Auto-Save (2 minutes)
```bash
AUTO_SAVE_INTERVAL_SECONDS=120
```

#### Disable Auto-Save (Manual Save Only)
```bash
AUTO_SAVE_INTERVAL_SECONDS=0
```

#### Production Configuration
```bash
STATE_ENCRYPTION_KEY=<your-secure-key-here>
ENABLE_PERSISTENCE=true
DATA_DIR=/opt/telegram-bot/data
BACKUP_RETENTION_COUNT=5
AUTO_SAVE_INTERVAL_SECONDS=300
LOG_LEVEL=INFO
```

## 🔒 Security

### Encryption Details

- **Algorithm**: Fernet (AES-128-CBC with HMAC-SHA256 for authentication)
- **Key Size**: 32 bytes (256 bits)
- **Token Expiry**: Fernet tokens include timestamps (for future expiry enforcement)
- **Integrity**: HMAC ensures tampering detection

### Key Management Best Practices

#### ✅ DO:
- **Generate keys** using `Fernet.generate_key()` (cryptographically secure)
- **Store keys** in environment variables (not in code)
- **Back up keys** securely (encrypted password manager, secrets vault)
- **Rotate keys** periodically (see migration guide below)
- **Use system secrets** management in production (Azure Key Vault, AWS Secrets Manager)
- **Restrict file permissions** (bot handles this automatically)

#### ❌ DON'T:
- **Commit keys** to version control
- **Share keys** via insecure channels (email, chat)
- **Use simple keys** like "password123" (always auto-generate)
- **Store keys** in source code or configuration files tracked by git
- **Lose keys** without backups (you'll lose access to encrypted data)

### File Permissions

The bot automatically sets secure permissions on all state files:

- **Unix/Linux**: `chmod 0600` (owner read/write only)
- **Windows**: ACL set to user-only access (via `icacls`)

### What If My Key Is Compromised?

1. **Generate a new key** immediately:
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Stop the bot**:
   ```powershell
   # Press Ctrl+C or kill the process
   ```

3. **Delete old encrypted data**:
   ```powershell
   Remove-Item data/tokens.enc
   Remove-Item data/backups/*.enc
   ```

4. **Update `.env` with new key**:
   ```
   STATE_ENCRYPTION_KEY=<new-key-here>
   ```

5. **Restart bot and re-authenticate**:
   ```powershell
   .\start-bot.bat
   # In Telegram: /connectoutlook
   ```

## 📂 File Structure

### State Directory Layout

```
data/
├── tokens.enc              # Encrypted Microsoft Graph token (Fernet)
├── user_state.json         # User task context (plain JSON)
├── .encryption_key         # Auto-generated key (if not in env var)
└── backups/
    ├── tokens.enc.1        # Most recent backup (newest)
    ├── tokens.enc.2        # Second backup
    ├── tokens.enc.3        # Third backup (oldest)
    ├── user_state.json.1   # Most recent state backup
    ├── user_state.json.2   # Second state backup
    └── user_state.json.3   # Third state backup (oldest)
```

### File Formats

#### `tokens.enc` (Encrypted Binary)
```
gAAAAABmX1Y2Z3... (Fernet-encrypted bytes)
```
Contains:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJub25jZSI6...",
  "timestamp": "2025-11-18T10:30:45.123456"
}
```

#### `user_state.json` (Plain JSON)
```json
{
  "version": "1.0",
  "users": {
    "123456789": {
      "id": "AAMkADExM...",
      "title": "Buy groceries",
      "due_date": "2025-11-20",
      "created_at": "2025-11-18T10:30:45.123456"
    }
  },
  "metadata": {
    "last_updated": "2025-11-18T10:35:12.654321"
  }
}
```

### Backup Rotation Strategy

1. **Before each save**, backups are rotated:
   - `file.ext.3` → **deleted** (oldest)
   - `file.ext.2` → `file.ext.3`
   - `file.ext.1` → `file.ext.2`
   - `file.ext` → `file.ext.1` (most recent)

2. **Then**, new state is saved to `file.ext`

3. **Retention** is configurable (default: 3 backups)

## 🔧 Troubleshooting

### Issue: "Invalid encryption key" error

**Symptoms:**
```
ERROR: Failed to initialize persistence: Invalid encryption key format
WARNING: Falling back to in-memory storage
```

**Solution:**
1. Check key is **base64-encoded** and exactly **32 bytes** when decoded
2. Regenerate a valid key:
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. Update `.env` and restart

### Issue: "Failed to decrypt token" warning

**Symptoms:**
```
WARNING: Failed to decrypt token: <error message>
WARNING: Backed up corrupted file to tokens.enc.corrupted.<timestamp>
```

**Causes:**
- Encryption key changed (different key than used to encrypt)
- File corrupted (disk error, incomplete write)
- Wrong file format (manually edited)

**Solution:**
1. Check if backup exists:
   ```powershell
   Get-ChildItem data/backups/tokens.enc.*
   ```
2. Restore from most recent backup:
   ```powershell
   Copy-Item data/backups/tokens.enc.1 data/tokens.enc
   ```
3. If no valid backup, re-authenticate:
   ```
   /connectoutlook
   ```

### Issue: "Permission denied" when writing state

**Symptoms:**
```
ERROR: Failed to save token state: [Errno 13] Permission denied: 'data/tokens.enc'
```

**Solution:**
1. **Check directory permissions**:
   ```powershell
   Get-Acl data
   ```
2. **Grant write access**:
   ```powershell
   # Windows
   icacls data /grant "%USERNAME%:(F)"
   ```
3. **Or change data directory**:
   ```
   DATA_DIR=C:\Users\YourName\AppData\Local\telegram-bot\data
   ```

### Issue: Auto-save not working

**Symptoms:**
- No log messages like "AutoSave: State saved"
- State not persisted between operations

**Solution:**
1. **Check interval** is not set to 0:
   ```
   AUTO_SAVE_INTERVAL_SECONDS=300
   ```
2. **Check logs** for thread errors:
   ```
   LOG_LEVEL=DEBUG
   ```
3. **Verify thread started**:
   Look for: `Auto-save thread started with 300s interval`

### Issue: "Data directory not writable" on startup

**Symptoms:**
```
ERROR: Data directory 'data' is not writable
```

**Solution:**
1. **Create directory** if missing:
   ```powershell
   New-Item -ItemType Directory -Path data
   New-Item -ItemType Directory -Path data\backups
   ```
2. **Check permissions** (see above)
3. **Try different directory**:
   ```
   DATA_DIR=%USERPROFILE%\.telegram-bot-data
   ```

## 🎓 Advanced Usage

### Manual State Management

#### Force Save State (Python Console)
```python
from src.utils import TokenManager, UserStateManager, EncryptionManager

# Initialize managers
enc_mgr = EncryptionManager("your-key-here")
token_mgr = TokenManager(
    encryption_manager=enc_mgr,
    token_file_path="data/tokens.enc",
    persistence_enabled=True
)
state_mgr = UserStateManager(
    state_file_path="data/user_state.json",
    persistence_enabled=True
)

# Force save
token_mgr.save_state()  # Returns True on success
state_mgr.save_state()  # Returns True on success
```

#### Load State Manually
```python
# Load saved state
tokens_loaded = token_mgr.load_state()
state_loaded = state_mgr.load_state()

print(f"Tokens loaded: {tokens_loaded}")
print(f"State loaded: {state_loaded}")
```

### Encryption Key Rotation

To rotate your encryption key without losing data:

1. **Decrypt with old key**:
   ```python
   from cryptography.fernet import Fernet
   
   old_key = "old-key-here"
   old_cipher = Fernet(old_key.encode())
   
   with open("data/tokens.enc", "rb") as f:
       encrypted_data = f.read()
   
   decrypted_data = old_cipher.decrypt(encrypted_data)
   ```

2. **Encrypt with new key**:
   ```python
   new_key = Fernet.generate_key().decode()
   new_cipher = Fernet(new_key.encode())
   
   re_encrypted_data = new_cipher.encrypt(decrypted_data)
   
   with open("data/tokens.enc", "wb") as f:
       f.write(re_encrypted_data)
   ```

3. **Update `.env`**:
   ```
   STATE_ENCRYPTION_KEY=<new-key-here>
   ```

### Backup and Restore

#### Create Manual Backup
```powershell
# Backup all state
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item data/tokens.enc "backups/tokens.enc.$timestamp"
Copy-Item data/user_state.json "backups/user_state.json.$timestamp"
```

#### Restore from Backup
```powershell
# List available backups
Get-ChildItem data/backups/ -Filter *.enc*

# Restore specific backup
Copy-Item data/backups/tokens.enc.1 data/tokens.enc
Copy-Item data/backups/user_state.json.1 data/user_state.json
```

### Migration Between Environments

#### Export State (Development → Production)
1. **Stop both bots**
2. **Copy state files**:
   ```powershell
   # On development machine
   Copy-Item data/tokens.enc \\production\share\
   Copy-Item data/user_state.json \\production\share\
   ```
3. **Copy encryption key** to production `.env`:
   ```
   STATE_ENCRYPTION_KEY=<same-key-from-dev>
   ```
4. **Start production bot**

#### Import State (Production → Development)
Same process, reverse direction. **Warning**: Development should use a separate Microsoft app registration to avoid conflicts.

## ✅ Best Practices

### Development
- Use auto-generated keys (convenience)
- Enable `LOG_LEVEL=DEBUG` for troubleshooting
- Commit `.env.template` (without keys) to git
- Use short auto-save intervals (60-120s) for testing

### Production
- Use manually generated keys (stored in secrets vault)
- Set `LOG_LEVEL=INFO` or `WARNING`
- Use system environment variables (not `.env` file)
- Use longer auto-save intervals (300-600s) to reduce I/O
- Monitor disk space in `data/` directory
- Set up automated backups of `data/` directory
- Use separate encryption keys per environment
- Rotate keys quarterly or after security incidents

### Security Checklist
- [ ] Encryption key stored in secrets manager (production)
- [ ] Encryption key backed up securely
- [ ] `.env` file excluded from git (via `.gitignore`)
- [ ] `data/` directory excluded from git
- [ ] File permissions restricted (handled automatically)
- [ ] Logs don't contain sensitive data (tokens, keys)
- [ ] Keys rotated quarterly or after incidents
- [ ] Backups stored on separate disk/location

### Monitoring
Monitor these log messages to ensure persistence is working:

✅ **Healthy:**
```
INFO: Persistence enabled - tokens: restored, state: restored
INFO: Auto-save thread started with 300s interval
INFO: AutoSave: State saved in 0.045s at 2025-11-18T10:35:12
```

⚠️ **Warning Signs:**
```
WARNING: Failed to save token state
WARNING: Failed to decrypt token
WARNING: AutoSave: User state save failed
ERROR: Failed to initialize persistence
```

## 📞 Support

If you encounter issues not covered in this guide:

1. **Enable debug logging**:
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Check bot logs** for error details

3. **Verify configuration**:
   - Encryption key valid base64
   - Data directory writable
   - Persistence enabled

4. **Try fallback to in-memory**:
   ```
   ENABLE_PERSISTENCE=false
   ```

5. **Open an issue** with:
   - Error message and stack trace
   - Configuration (without sensitive keys)
   - Steps to reproduce

---

**Last Updated**: November 2025  
**Version**: 1.4.0 (Persistent State Management)
