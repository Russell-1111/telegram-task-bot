# Design: Multi-Tenancy and Async I/O Refactoring

## Context

The Telegram Task Bot currently supports single-user token storage and uses synchronous blocking I/O for all Microsoft Graph API interactions. This architecture was sufficient for initial development and single-user testing, but fails to support production requirements:

- **Concurrency:** Multiple Telegram users cannot interact with the bot simultaneously without token overwrites
- **Responsiveness:** Synchronous HTTP calls block the asyncio event loop, freezing the bot during API requests
- **Scalability:** The bot cannot handle multiple simultaneous task operations without degrading user experience

This refactoring corrects these fundamental limitations by implementing per-user token isolation and non-blocking I/O patterns.

## Goals / Non-Goals

**Goals:**
- Enable true multi-user support with isolated authentication sessions per Telegram user
- Eliminate event loop blocking during Microsoft Graph API calls
- Maintain backward compatibility for persistence file formats (with migration)
- Preserve all existing bot functionality (commands, task creation, task listing)
- Ensure zero data loss during migration from single-tenant to multi-tenant storage

**Non-Goals:**
- Token refresh logic (deferred to future work; users re-authenticate when tokens expire)
- Database-backed token storage (file-based encryption remains, scaled for multi-user)
- Horizontal scaling across multiple bot instances (single-instance multi-user is the target)
- Advanced async optimizations like connection pooling or request batching (future enhancements)

## Decisions

### Decision 1: Multi-Tenant Storage Structure

**Choice:** Use `Dict[int, TokenData]` where `int` is Telegram `user_id` and `TokenData` is a dataclass containing `access_token: str` and `set_at: datetime`.

**Rationale:**
- Simple in-memory lookup by user ID with O(1) access time
- Directly maps to Telegram's user identification model (`update.effective_user.id`)
- Dataclass provides type safety and clear structure for token metadata
- Easily serializable to JSON for encrypted persistence

**Alternatives Considered:**
1. **Single token with user ID tagging:** Keep single token but track which user it belongs to → Rejected because it doesn't solve the overwriting problem; still single-session
2. **Database storage (SQLite/PostgreSQL):** Use database for token storage → Rejected as over-engineering for current scale; adds deployment complexity without clear benefit for single-instance bot
3. **LRU cache with eviction:** Limit stored tokens to N most recent users → Rejected because it forces re-authentication unpredictably; all authenticated users should remain valid until token expiration

### Decision 2: Async I/O Implementation Strategy

**Choice:** Refactor `OutlookService` to `async def` methods and use `httpx.AsyncClient` for HTTP calls. Wrap blocking `outlook_api` functions in `asyncio.to_thread` initially, with future full refactor to async.

**Rationale:**
- `httpx` is a modern, well-maintained async HTTP client with similar API to `requests`
- `asyncio.to_thread` allows incremental migration by running blocking code in executor threads
- Telegram bot handlers are already async (`async def`), so service layer should match
- Non-blocking I/O prevents event loop starvation and enables concurrent user operations

**Alternatives Considered:**
1. **Keep synchronous, run in executor at handler level:** Use `asyncio.to_thread` only in handlers → Rejected because it pushes concurrency management to wrong layer; service layer should own I/O patterns
2. **Use `aiohttp` instead of `httpx`:** → Rejected because `httpx` has better API ergonomics and compatibility with `requests` patterns
3. **Full async rewrite of `outlook_api.py`:** Eliminate blocking functions entirely → Deferred to future; `asyncio.to_thread` wrapper is sufficient for immediate fix and maintains code stability

### Decision 3: Breaking Change Management

**Choice:** Accept breaking changes to `TokenManager` API and update all call sites in a single atomic commit.

**Rationale:**
- The single-tenancy flaw is critical and must be fixed; breaking changes are unavoidable
- All call sites are within the same codebase and can be updated together
- No external consumers of `TokenManager` API (internal module only)
- Clear migration path: search for `token_manager.set_token(` and add `user_id` argument

**Alternatives Considered:**
1. **Add new methods, deprecate old:** Create `set_token_for_user(user_id, token)` and deprecate `set_token(token)` → Rejected because deprecation period doesn't make sense for internal API with critical flaw
2. **Use default user ID for backward compatibility:** Allow `set_token(token)` to default to `user_id=0` → Rejected because it hides the multi-tenancy requirement and encourages incorrect usage

### Decision 4: Persistence Migration Strategy

**Choice:** Implement automatic migration on first load. Detect old format (single-token JSON), wrap in multi-user dictionary with sentinel `user_id=-1`, save in new format.

**Rationale:**
- Zero manual intervention required from operators
- Preserves existing token if present (avoids immediate re-authentication on upgrade)
- Sentinel user ID (-1) clearly indicates legacy token and can be cleaned up later
- One-time migration cost, all subsequent operations use new format

**Migration Flow:**
```
1. Bot starts, attempts to load tokens.enc
2. Decrypt and parse JSON
3. If JSON is old format (has "access_token" key at root):
   - Wrap in {"tokens": {-1: {"access_token": "...", "set_at": "..."}}}
   - Save in new format
4. If JSON is new format (has "tokens" dictionary key):
   - Load directly
5. Continue operation with new format
```

**Alternatives Considered:**
1. **Force re-authentication on upgrade:** Delete old tokens, require all users to re-authenticate → Rejected as poor UX; migration should be transparent
2. **Manual migration script:** Provide `migrate_tokens.py` script → Rejected as unnecessary complexity; automatic migration is simpler
3. **Support both formats indefinitely:** → Rejected because it increases code complexity and tech debt

### Decision 5: Async Initialization Handling

**Choice:** Make `TokenManager.load_state()` and `UserStateManager.load_state()` remain synchronous. Perform all persistence I/O during bot startup before asyncio loop starts.

**Rationale:**
- Startup operations are one-time and don't need to be async
- Simplifies initialization flow in `bot.py`
- Persistence load is fast (single file read + decrypt) and doesn't justify async overhead
- Telegram bot framework handles async runtime after initialization

**Alternatives Considered:**
1. **Make `load_state()` async:** Convert to `async def` and use `asyncio.run()` → Rejected as over-engineering; startup I/O is acceptable to block

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot (bot.py)                     │
│  - Initializes TokenManager with multi-user storage          │
│  - Starts async event loop for message handling              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Handlers (command_handlers.py)                 │
│  - Extract user_id = update.effective_user.id                │
│  - Pass user_id to TokenManager.get_token(user_id)           │
│  - await OutlookService async methods                        │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌────────────────────┐       ┌────────────────────────────┐
│   TokenManager     │       │    OutlookService          │
│  (Multi-Tenant)    │       │    (Async I/O)             │
│                    │       │                            │
│ _tokens: Dict[int, │       │ async def authenticate()   │
│   TokenData]       │       │ async def create_task()    │
│                    │       │ async def get_tasks()      │
│ set_token(user_id) │       │   → uses httpx.AsyncClient │
│ get_token(user_id) │       │   → or asyncio.to_thread   │
└─────────┬──────────┘       └─────────────┬──────────────┘
          │                                 │
          ▼                                 ▼
┌────────────────────┐       ┌────────────────────────────┐
│  Encrypted Storage │       │  Microsoft Graph API       │
│  (tokens.enc)      │       │  (https://graph.microsoft) │
│  Multi-user JSON   │       │  Non-blocking HTTP calls   │
└────────────────────┘       └────────────────────────────┘
```

## Data Model Changes

### Old TokenManager Structure (Single-Tenant)
```python
class TokenManager:
    _access_token: Optional[str]  # Single global token
    _token_set_at: Optional[datetime]
```

**Encrypted File Format (Old):**
```json
{
  "version": "1.0",
  "access_token": "eyJ0eXAiOiJKV1QiLC...",
  "token_set_at": "2025-11-19T10:00:00",
  "metadata": {
    "encrypted_at": "2025-11-19T10:00:00"
  }
}
```

### New TokenManager Structure (Multi-Tenant)
```python
@dataclass
class TokenData:
    access_token: str
    set_at: datetime

class TokenManager:
    _tokens: Dict[int, TokenData]  # user_id -> TokenData
```

**Encrypted File Format (New):**
```json
{
  "version": "2.0",
  "tokens": {
    "123456789": {
      "access_token": "eyJ0eXAiOiJKV1QiLC...",
      "set_at": "2025-11-19T10:00:00"
    },
    "987654321": {
      "access_token": "eyJ0eXAiOiJKV1QiLC...",
      "set_at": "2025-11-19T10:05:00"
    }
  },
  "metadata": {
    "encrypted_at": "2025-11-19T10:05:00"
  }
}
```

## API Changes

### TokenManager (Breaking Changes)

**Before:**
```python
# Single-tenant API
token_manager.set_token(token)
token = token_manager.get_token()
has_token = token_manager.has_token()
age = token_manager.get_token_age()
```

**After:**
```python
# Multi-tenant API (user_id required)
user_id = update.effective_user.id
token_manager.set_token(user_id, token)
token = token_manager.get_token(user_id)
has_token = token_manager.has_token(user_id)
age = token_manager.get_token_age(user_id)
```

### OutlookService (Async Conversion)

**Before:**
```python
# Synchronous (blocking)
def create_task(access_token, title, due_date):
    # Blocks event loop during HTTP request
    response = requests.post(url, json=data)
    return response.json()

# Handler (synchronous)
async def handle_command(update, context):
    token = token_manager.get_token()
    task = outlook_service.create_task(token, "Buy milk", "2025-11-20")
    # Event loop blocked during create_task
```

**After:**
```python
# Asynchronous (non-blocking)
async def create_task(access_token, title, due_date):
    # Non-blocking HTTP request
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Handler (asynchronous)
async def handle_command(update, context):
    user_id = update.effective_user.id
    token = token_manager.get_token(user_id)
    task = await outlook_service.create_task(token, "Buy milk", "2025-11-20")
    # Event loop free during HTTP request
```

## Migration Plan

### Phase 1: TokenManager Multi-Tenancy (Breaking)
1. Define `TokenData` dataclass in `token_manager.py`
2. Replace `_access_token` and `_token_set_at` with `_tokens: Dict[int, TokenData]`
3. Update all methods to accept `user_id: int` as first argument (after `self`)
4. Implement migration logic in `_load_from_disk()` to detect and upgrade old format
5. Update `_save_to_disk()` to serialize multi-user dictionary
6. Run existing unit tests (will fail) and update test call sites
7. Update all handler call sites to pass `user_id`

**Rollback Strategy:** Revert commit if tests fail after handler updates. Old format files are preserved as backups automatically.

### Phase 2: OutlookService Async Conversion (Non-Breaking)
1. Add `httpx` to `requirements.txt`
2. Convert `OutlookService` methods to `async def`
3. Replace `outlook_api` blocking calls with `asyncio.to_thread(outlook_api.function, ...)`
4. Update handler call sites to use `await outlook_service.method()`
5. Test concurrent operations (multiple users creating tasks simultaneously)

**Rollback Strategy:** If async causes issues, revert async changes and keep multi-tenancy (Phase 1 is independent).

### Phase 3: Full Async Refactor (Future, Optional)
1. Refactor `outlook_api.py` to use `httpx.AsyncClient` directly
2. Remove `asyncio.to_thread` wrappers in `OutlookService`
3. Optimize connection pooling and request batching

**Note:** Phase 3 is a future enhancement and not required for this proposal.

## Risks / Trade-offs

### Risk 1: Migration Failure on Corrupt Files
**Mitigation:** Existing backup and corruption recovery logic (`_backup_corrupted_file`) handles this. If migration fails, bot falls back to empty state and logs error. Users re-authenticate.

### Risk 2: Increased Memory Usage with Multi-User Tokens
**Trade-off:** Each token is ~1-2 KB. For 1000 users, total memory ~2 MB (negligible). Acceptable trade-off for multi-user support.

### Risk 3: Breaking Changes Require Coordinated Update
**Mitigation:** All code is in single repository. Single atomic commit updates all call sites. No partial deployment risk.

### Risk 4: Async Conversion Introduces New Concurrency Bugs
**Mitigation:** 
- Start with conservative approach (`asyncio.to_thread` wrappers)
- Add unit tests for concurrent operations (multiple users creating tasks)
- Existing Telegram bot framework handles async correctly (proven pattern)

### Risk 5: Token Expiration Not Handled
**Known Limitation:** Tokens expire after ~1 hour. Users must re-authenticate. This is existing behavior; not changed by refactoring. Future work: implement token refresh flow.

## Open Questions

1. **Q:** Should we add token expiration warnings before tokens expire?
   **A:** Deferred to future work. Current behavior (re-authenticate on error) is acceptable.

2. **Q:** Should we limit the number of stored tokens (e.g., LRU eviction)?
   **A:** No. File size is manageable even with 1000s of users (~1-2 MB). Explicit cleanup command can be added later if needed.

3. **Q:** Should we add metrics/logging for token usage per user?
   **A:** Yes, add INFO-level logs for token operations with user ID for debugging. No metrics infrastructure yet.

4. **Q:** Should we add API rate limiting per user to prevent abuse?
   **A:** Out of scope for this change. Existing per-command rate limiting (e.g., `/mytasks` 1/minute) remains. Per-user global rate limiting is future work.
