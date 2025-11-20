# Proposal: Refactor Multi-Tenancy and Async I/O

## Why

The current architecture suffers from two critical flaws that prevent the bot from functioning correctly in production:

1. **Single-Tenancy (Critical Flaw):** The `TokenManager` stores only one access token globally in a single `_access_token` string variable. This means every new user authentication immediately overwrites the previous session, breaking multi-user functionality and creating a poor user experience. If User A authenticates and then User B authenticates, User A's token is lost, and their session becomes invalid.

2. **Blocking I/O:** The `OutlookService` and underlying `outlook_api` module rely on synchronous I/O operations (HTTP API calls via `requests` library and disk access for persistence), which block the asyncio event loop. This degrades bot responsiveness, prevents concurrent task handling, and limits scalability. Every API call to Microsoft Graph freezes the bot for all users until the response arrives.

These are not optimizations—they are fundamental architectural defects that must be corrected for the bot to support multiple concurrent users and maintain acceptable performance.

## What Changes

### 1. Multi-Tenancy Enforcement (TokenManager)
- **Structural Change:** Modify `TokenManager` internal storage from a single `_access_token: Optional[str]` to a dictionary mapping `user_id: int` to token data: `_tokens: Dict[int, TokenData]` where `TokenData` is a dataclass containing `access_token: str` and `set_at: datetime`.
- **Core API Modification (BREAKING):** All token manipulation methods are updated to enforce per-user storage:
    - `set_token(user_id: int, token: str)` - signature modified to accept mandatory `telegram_user_id` argument
    - `get_token(user_id: int)` - signature modified to accept mandatory `telegram_user_id` argument
    - **Utility Methods:** Update all auxiliary methods: `has_token(user_id: int)`, `clear_token(user_id: int)`, `get_token_age(user_id: int)`, and `get_token_info(user_id: int)`.
- **Persistence Rework:** Refactor `_save_to_disk` and `_load_from_disk` logic to serialize and deserialize the **full dictionary** of multi-user token data securely. The encrypted file format changes from single-token JSON to multi-token dictionary JSON.

### 2. Asynchronous I/O Integration
- **OutlookService:** All I/O-bound methods in `OutlookService` must be updated to **`async def`**:
    - `async def authenticate(user_id: int)` 
    - `async def create_task(access_token: str, ...)`
    - `async def update_task_due_date(access_token: str, ...)`
    - `async def get_uncompleted_tasks(access_token: str, ...)`
    - `async def get_all_tasks(access_token: str)`
    - `async def delete_task(access_token: str, task_id: str)`
- **Blocking Call Handling:** Implement non-blocking execution within these methods by:
    - Refactoring to use `httpx.AsyncClient` instead of `requests` for HTTP calls
    - Using `asyncio.to_thread` to run blocking `outlook_api` functions in a thread pool executor
- **Dependency Update:** All upstream handlers in `command_handlers.py` and `message_handlers.py` must use `await` when calling `OutlookService` methods.

### 3. Handler & Integration Updates
- **Handler Refactoring:** Modify `src/handlers/command_handlers.py` and `src/handlers/message_handlers.py` to:
    - Explicitly retrieve `user_id = update.effective_user.id` at the start of each handler
    - Pass the `user_id` to **all** subsequent calls to `TokenManager` methods
    - Use `await` for all `OutlookService` method calls
- **Initialization:** Update `src/bot.py` to ensure persistence loading works correctly with multi-user token structure and async initialization if needed.

### 4. New Capability: User Authentication (Spec Creation)
- **Create New Spec:** `openspec/specs/user-authentication/spec.md` to formally define:
    - Multi-user token isolation requirements
    - Per-user authentication lifecycle
    - Token validation and expiration rules
    - User identity verification from Telegram context

## Impact

| Area | Impact Summary |
|:-----|:--------------|
| **Multi-Tenancy** | **CRITICAL FIX:** Enables simultaneous, isolated sessions for multiple users. Overwriting of tokens is eliminated. Each user's token is stored independently and retrieved by their unique Telegram user ID. |
| **Performance** | **HIGH IMPROVEMENT:** Non-blocking I/O prevents event loop starvation, drastically increasing bot responsiveness and concurrency. Multiple users can interact with the bot simultaneously without blocking each other. |
| **Affected Specs** | **CREATED:** `user-authentication` (new capability for multi-tenancy rules). **MODIFIED:** `state-persistence` (for multi-user data structure). |
| **Affected Files** | `src/utils/token_manager.py`, `src/services/outlook_service.py`, `src/handlers/command_handlers.py`, `src/handlers/message_handlers.py`, `src/bot.py`, `outlook_api.py` (if refactored), tests for all modified modules. |
| **Breaking Changes** | **INTENTIONAL:** The API signatures for all public `TokenManager` methods must now accept `user_id: int`, breaking compatibility with the single-tenant model. This is necessary to correct the underlying design flaw. All call sites must be updated. |
| **Migration Path** | Existing single-token encrypted files will be migrated on first load: the bot will read the old format, wrap it in a dictionary keyed by a sentinel value (e.g., `user_id=-1`), and save in the new format. Operators should re-authenticate all users after upgrade to establish proper per-user tokens. |
| **Testing** | New unit tests required for multi-user token isolation, async I/O behavior, and concurrent operations. Existing tests must be updated to provide `user_id` arguments. |
| **Deployment** | Rolling restart required. Users will need to re-authenticate via `/connectoutlook` after deployment to establish per-user tokens. Downtime: none (graceful restart). |
