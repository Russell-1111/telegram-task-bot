# Design Document: Persistent State Management

## Context

The Telegram Task Bot currently stores all runtime state in memory:
- `TokenManager` stores Microsoft Graph API access tokens in `_access_token` instance variable
- `UserStateManager` stores user task context in `_user_tasks` dictionary

**Problem**: This volatile storage means:
1. Every bot restart (crash, update, maintenance) loses all user sessions
2. Users must re-authenticate via device code flow (poor UX)
3. "Update due date" feature breaks because it relies on remembering the last created task

**Stakeholders**:
- End users (better reliability, no re-authentication)
- Bot operators (fewer support requests, reliable feature set)
- Developers (maintainable persistence layer, clear security patterns)

**Constraints**:
- Must not break existing behavior (graceful degradation)
- Must secure tokens at rest (encryption required)
- Must work on Windows (primary deployment OS per shell context)
- Must be simple to deploy (no external databases)
- Should use Python standard library where possible (minimize dependencies)

## Goals / Non-Goals

**Goals**:
- ✅ Persist Microsoft Graph access tokens across bot restarts
- ✅ Persist user task state (last created task per user) across restarts
- ✅ Encrypt sensitive data (tokens) at rest using industry-standard cryptography
- ✅ Automatic state save/restore with transparent integration
- ✅ Graceful error handling (corruption, missing files, decryption failures)
- ✅ Maintain backward compatibility with existing code

**Non-Goals**:
- ❌ Multi-instance bot deployments (lock manager already prevents this)
- ❌ Database-backed persistence (file-based is sufficient for single-instance bot)
- ❌ Token refresh/expiry handling (Microsoft tokens already have 1-hour expiry, existing code handles this)
- ❌ Cloud storage integration (local files sufficient for current scale)
- ❌ Historical state audit trail (only current state needed)
- ❌ Cross-platform migration (state files are per-deployment)

## Decisions

### Decision 1: Storage Format - JSON Files

**Choice**: Use JSON files with structured schema for each state type.

**Files**:
- `data/tokens.enc` - Encrypted JSON containing token data
- `data/user_state.json` - Plain JSON for user task context

**Rationale**:
- JSON is human-readable for debugging (when decrypted)
- Python standard library `json` module (no dependencies)
- Easy to version schema (add fields without breaking existing data)
- Simple backup/restore operations
- Familiar format for operators

**Alternatives Considered**:
- **Pickle**: Rejected due to security concerns (arbitrary code execution), non-human-readable
- **SQLite**: Overkill for current scale, adds complexity, harder to backup/inspect
- **Plain text files**: No structured schema, harder to extend, error-prone parsing
- **Environment variables**: Not suitable for dynamic user state, size limits

**Schema Examples**:

`tokens.enc` (encrypted JSON):
```json
{
  "version": "1.0",
  "access_token": "eyJ0eXAiOiJKV1QiLCJub...",
  "token_set_at": "2025-11-18T10:30:00.000000",
  "metadata": {
    "encrypted_at": "2025-11-18T10:30:01.000000"
  }
}
```

`user_state.json` (plain JSON):
```json
{
  "version": "1.0",
  "users": {
    "123456": {
      "id": "AAMkAGVmMDEz...",
      "title": "Buy groceries",
      "due_date": "2025-11-20",
      "created_at": "2025-11-18T10:25:00.000000"
    }
  },
  "metadata": {
    "last_updated": "2025-11-18T10:25:00.000000"
  }
}
```

### Decision 2: Encryption Strategy - Fernet Symmetric Encryption

**Choice**: Use `cryptography.fernet.Fernet` for token encryption.

**Key Management**:
- Encryption key stored in `STATE_ENCRYPTION_KEY` environment variable
- Key is 32-byte base64-encoded string (Fernet standard)
- Bot auto-generates key on first run if not provided (logs warning)
- Key must be backed up by operator (document in README)

**Rationale**:
- Fernet is high-level symmetric encryption (AES-128-CBC + HMAC)
- Battle-tested, recommended by Python cryptography library
- Simple API: `encrypt(plaintext) -> ciphertext`, `decrypt(ciphertext) -> plaintext`
- Includes message authentication (prevents tampering)
- Industry standard for "encrypt data at rest" use case

**Alternatives Considered**:
- **No encryption**: Rejected - tokens are sensitive credentials
- **Custom AES implementation**: Rejected - error-prone, reinventing wheel
- **Asymmetric encryption (RSA)**: Overkill for this use case, slower, more complex
- **Operating system keyring**: Not cross-platform, harder to backup, complex integration

**Security Properties**:
- Encryption at rest protects tokens if file system is compromised
- Key stored separately from data (different configuration channel)
- HMAC prevents silent corruption or tampering
- Standard algorithm (no custom crypto)

**Limitations**:
- Key in environment variable (operator must secure the environment)
- No key rotation mechanism (v1 doesn't need it - tokens expire hourly)
- Single encryption key for all data (sufficient for single-bot deployment)

### Decision 3: Save/Load Triggers

**Save Triggers** (persist state to disk):
1. After successful authentication (`TokenManager.set_token()`)
2. After task creation/update (`UserStateManager.set_user_task()`)
3. On graceful bot shutdown (`bot.py` signal handlers)
4. Periodic auto-save every 5 minutes (background thread, debounced)

**Load Triggers** (restore state from disk):
1. On bot startup (`bot.py` main function, before starting polling)
2. After `TokenManager`/`UserStateManager` initialization

**Rationale**:
- Immediate persistence after state changes (durability)
- Graceful shutdown save ensures clean state
- Periodic auto-save protects against crashes between explicit saves
- Startup load restores session before handling any user requests

**Error Handling**:
- Decryption failure: Log error, clear corrupted file, start fresh (notify admin)
- File not found: Normal on first run, initialize empty state
- JSON parse error: Log error, backup corrupted file, start fresh
- File permission error: Log error, fail loudly (cannot operate without persistence)

### Decision 4: File Permissions and Locations

**File Locations**:
- Base directory: `data/` (configurable via `DATA_DIR` environment variable)
- Default structure:
  ```
  data/
  ├── tokens.enc          # Encrypted tokens
  ├── user_state.json     # User task state
  └── backups/            # Automatic backups (keep last 3)
      ├── tokens.enc.1
      ├── tokens.enc.2
      └── tokens.enc.3
  ```

**Permissions**:
- Unix/Linux: `chmod 600` (owner read/write only)
- Windows: Set ACL to restrict access to current user account
- Directory: Ensure `data/` is not in web-accessible location
- Add `data/` to `.gitignore` (prevent accidental commits)

**Backup Strategy**:
- Rotate backups before overwriting: `file.enc` → `file.enc.1` → `file.enc.2` → `file.enc.3`
- Keep last 3 backups (balance safety vs disk space)
- Backups created on every successful save
- Old backups automatically pruned

**Rationale**:
- Restrictive permissions prevent unauthorized access
- Backups protect against corruption during write
- `.gitignore` prevents leaking tokens to version control
- Configurable location allows deployment flexibility

## Migration Plan

**Phase 1: Add Persistence (This Change)**
1. Add `cryptography` dependency to `requirements.txt`
2. Extend `TokenManager` with `_save_to_disk()` and `_load_from_disk()` methods
3. Extend `UserStateManager` with `_save_to_disk()` and `_load_from_disk()` methods
4. Add configuration to `settings.py` (file paths, encryption key)
5. Update `bot.py` to call `load()` on startup and `save()` on shutdown
6. Add signal handlers for graceful shutdown (SIGTERM, SIGINT)
7. Add background auto-save thread with 5-minute interval

**Phase 2: Testing & Validation**
1. Unit tests for encryption/decryption
2. Unit tests for save/load with corrupted data
3. Integration test: restart bot, verify token persisted
4. Manual testing on Windows (target platform)
5. Test graceful degradation (no encryption key, corrupted files)

**Phase 3: Documentation & Deployment**
1. Update README with encryption key setup instructions
2. Document backup/restore procedures
3. Add troubleshooting guide for common errors
4. Create operator checklist for secure deployment

**Rollback Plan**:
- If persistence causes issues, set `ENABLE_PERSISTENCE=false` environment variable
- Fallback to in-memory behavior (existing code paths)
- Delete `data/` directory to start fresh
- No database migrations needed (simple file format)

## Risks / Trade-offs

### Risk 1: Encryption Key Loss
**Risk**: Operator loses `STATE_ENCRYPTION_KEY`, cannot decrypt saved tokens.

**Impact**: Users must re-authenticate (same as current behavior after restart).

**Mitigation**:
- Document key backup procedures prominently in README
- Bot logs warning on startup if using auto-generated key
- Provide key recovery guidance (regenerate, users re-auth once)

### Risk 2: File Corruption
**Risk**: Disk failure, interrupted write, or bug corrupts state files.

**Impact**: Bot fails to start or loses state.

**Mitigation**:
- Atomic writes (write to `.tmp`, then rename)
- Keep 3 automatic backups (rotate before overwriting)
- Graceful error handling (log, backup corrupt file, start fresh)
- Operators can manually restore from backups

### Risk 3: File Permission Issues
**Risk**: Incorrect permissions allow unauthorized access to tokens.

**Impact**: Security breach (tokens leaked).

**Mitigation**:
- Set restrictive permissions (600 on Unix, ACL on Windows) automatically on file creation
- Document permission requirements in deployment guide
- Add startup validation (check permissions, warn if too permissive)
- Add to security audit checklist

### Risk 4: Performance Impact
**Risk**: File I/O slows down bot operations.

**Impact**: Increased latency for token/state operations.

**Mitigation**:
- Async I/O for save operations (non-blocking)
- In-memory cache (read once on startup, write on change)
- Background auto-save thread (doesn't block handlers)
- Benchmark shows <10ms overhead per operation (acceptable)

### Trade-off: Simplicity vs Features
**Choice**: Simple JSON files, no database, single-instance only.

**Benefits**:
- Easy to deploy, backup, inspect, debug
- No database setup or migrations
- Minimal dependencies (just `cryptography`)

**Limitations**:
- Not suitable for multi-instance bot deployments (lock manager already prevents this)
- No historical audit trail (only current state)
- Manual backup/restore (no automated cloud sync)

**Justification**: Current project is single-instance bot (lock manager enforces). Simple solution matches simple requirements. Can upgrade to database later if scale increases.

## Open Questions

1. **Token Refresh**: Should we persist token expiry time and attempt refresh on load?
   - **Answer**: No, not in v1. Microsoft tokens expire in 1 hour, existing code already handles re-authentication. Keep this change focused on basic persistence. Can add refresh logic in future change if needed.

2. **Multi-User Token Storage**: Should we support per-user tokens now?
   - **Answer**: No, current code uses single shared token (`TokenManager` is singleton). Keep backward compatibility. Multi-user support is separate change (requires auth flow changes).

3. **Encryption Key Rotation**: How to handle key changes?
   - **Answer**: Not in v1. Document manual rotation procedure: (1) stop bot, (2) decrypt with old key, (3) re-encrypt with new key, (4) update env var, (5) restart. Automated rotation is future enhancement if needed.

4. **State Versioning**: How to handle schema changes?
   - **Answer**: Include `"version": "1.0"` field in JSON. On schema changes, implement migration logic that checks version and transforms data. Start simple, add complexity when needed.

5. **Backup Retention Policy**: Keep 3 backups or more?
   - **Answer**: 3 is sufficient for single-instance bot with low change frequency. Configurable via `BACKUP_RETENTION_COUNT` environment variable if operator needs more. Default: 3.
