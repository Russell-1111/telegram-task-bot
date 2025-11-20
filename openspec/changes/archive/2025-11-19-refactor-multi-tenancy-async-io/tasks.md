# Implementation Tasks

## 1. TokenManager Multi-Tenancy Refactoring

- [x] 1.1 Create `TokenData` dataclass in `src/utils/token_manager.py` with `access_token: str` and `set_at: datetime` fields
- [x] 1.2 Replace `_access_token` and `_token_set_at` instance variables with `_tokens: Dict[int, TokenData]`
- [x] 1.3 Update `set_token()` signature to `set_token(self, user_id: int, token: str)` and implement multi-user storage
- [x] 1.4 Update `get_token()` signature to `get_token(self, user_id: int)` and implement multi-user retrieval
- [x] 1.5 Update `has_token()` signature to `has_token(self, user_id: int)` and check user-specific existence
- [x] 1.6 Update `clear_token()` signature to `clear_token(self, user_id: int)` and implement user-specific deletion
- [x] 1.7 Update `get_token_age()` signature to `get_token_age(self, user_id: int)` and compute age for specific user
- [x] 1.8 Update `get_token_info()` signature to `get_token_info(self, user_id: int)` and return user-specific info
- [x] 1.9 Update `_save_to_disk()` to serialize multi-user token dictionary (version 2.0 format)
- [x] 1.10 Update `_load_from_disk()` to deserialize multi-user token dictionary
- [x] 1.11 Implement migration logic in `_load_from_disk()` to detect version 1.0 and upgrade to version 2.0
- [x] 1.12 Add logging for all token operations with user ID included in log messages
- [x] 1.13 Update unit tests in `tests/test_token_manager.py` to provide `user_id` in all method calls
- [x] 1.14 Add new unit tests for multi-user token isolation (User A token does not affect User B)
- [x] 1.15 Add new unit tests for migration from version 1.0 to version 2.0
- [x] 1.16 Run tests with `pytest tests/test_token_manager.py -v` and verify all pass

## 2. Handler Call Site Updates

- [x] 2.1 Update `src/handlers/command_handlers.py` to extract `user_id = update.effective_user.id` at the start of each handler
- [x] 2.2 Update `connect_outlook()` handler to call `token_manager.set_token(user_id, token)`
- [x] 2.3 Update `my_tasks()` handler to call `token_manager.get_token(user_id)` and `token_manager.has_token(user_id)`
- [x] 2.4 Update `set_outlook_token()` function to accept `user_id` parameter: `set_outlook_token(user_id, token)`
- [x] 2.5 Update `get_outlook_token()` function to accept `user_id` parameter: `get_outlook_token(user_id)`
- [x] 2.6 Update `src/handlers/message_handlers.py` to extract `user_id = update.effective_user.id` at the start of each handler
- [x] 2.7 Update all `token_manager.has_token()` calls in `message_handlers.py` to pass `user_id`
- [x] 2.8 Update all `token_manager.get_token()` calls in `message_handlers.py` to pass `user_id`
- [x] 2.9 Update `set_managers()` function docstring to document user_id extraction requirement
- [x] 2.10 Run tests with `pytest tests/handlers/ -v` and verify all pass

## 3. OutlookService Async Conversion

- [x] 3.1 Add `httpx` to `requirements.txt` (e.g., `httpx>=0.24.0`)
- [x] 3.2 Convert `authenticate()` to `async def authenticate(self)` in `src/services/outlook_service.py`
- [x] 3.3 Wrap `outlook_api.get_auth_token()` call with `asyncio.to_thread()` in `authenticate()`
- [x] 3.4 Convert `create_task()` to `async def create_task(self, access_token, task_title, due_date_iso=None)`
- [x] 3.5 Wrap `outlook_api.create_outlook_task()` call with `asyncio.to_thread()` in `create_task()`
- [x] 3.6 Convert `update_task_due_date()` to `async def update_task_due_date(self, access_token, task_id, new_due_date_iso)`
- [x] 3.7 Wrap `outlook_api.update_task_due_date()` call with `asyncio.to_thread()` in `update_task_due_date()`
- [x] 3.8 Convert `get_uncompleted_tasks()` to `async def get_uncompleted_tasks(self, access_token, max_tasks=10)`
- [x] 3.9 Wrap `outlook_api.get_uncompleted_tasks()` call with `asyncio.to_thread()` in `get_uncompleted_tasks()`
- [x] 3.10 Convert `get_all_tasks()` to `async def get_all_tasks(self, access_token)`
- [x] 3.11 Wrap `outlook_api.get_all_tasks()` call with `asyncio.to_thread()` in `get_all_tasks()`
- [x] 3.12 Convert `delete_task()` to `async def delete_task(self, access_token, task_id)`
- [x] 3.13 Wrap `outlook_api.delete_task()` call with `asyncio.to_thread()` in `delete_task()`
- [x] 3.14 Update all docstrings in `OutlookService` to indicate async behavior
- [x] 3.15 Update `connect_outlook()` handler in `command_handlers.py` to use `await outlook_service.authenticate()`
- [x] 3.16 Update `my_tasks()` handler in `command_handlers.py` to use `await outlook_service.get_uncompleted_tasks(...)`
- [x] 3.17 Update all `outlook_service` calls in `message_handlers.py` to use `await`
- [x] 3.18 Run tests with `pytest tests/services/test_outlook_service.py -v` and verify all pass
- [x] 3.19 Update tests to use `pytest-asyncio` and `@pytest.mark.asyncio` decorators for async tests

## 4. Integration and End-to-End Testing

- [x] 4.1 Create integration test: User A authenticates, User B authenticates, both tokens stored independently
- [x] 4.2 Create integration test: User A creates task, User B creates task concurrently, no race conditions
- [x] 4.3 Create integration test: Bot restarts, all users' tokens restored correctly from encrypted file
- [x] 4.4 Create integration test: Migration from version 1.0 token file to version 2.0
- [x] 4.5 Create integration test: Concurrent token save and auto-save thread do not corrupt data
- [x] 4.6 Create integration test: Async OutlookService calls do not block event loop (measure latency)
- [x] 4.7 Run full test suite with `pytest tests/ -v --cov=src` and verify coverage ≥90% for modified modules
- [x] 4.8 Fix any failing tests and re-run until all pass

## 5. Documentation Updates

- [x] 5.1 Update `TokenManager` docstring in `src/utils/token_manager.py` to document multi-tenancy
- [x] 5.2 Update `OutlookService` docstring in `src/services/outlook_service.py` to document async behavior
- [x] 5.3 Update `README.md` to note multi-user support and async architecture
- [x] 5.4 Update `docs/ARCHITECTURE-REVIEW.md` to document multi-tenant token storage structure
- [x] 5.5 Update `docs/PERSISTENCE-GUIDE.md` to document version 2.0 file format
- [x] 5.6 Add migration notes to `docs/SETUP.md` for operators upgrading from single-tenant bot

## 6. Manual Testing and Validation

- [x] 6.1 Start bot locally with persistence enabled
- [x] 6.2 Test User A authentication via `/connectoutlook` and verify token saved
- [x] 6.3 Test User B authentication via `/connectoutlook` and verify both tokens saved independently
- [x] 6.4 Test User A task creation and verify User A's token used
- [x] 6.5 Test User B task creation and verify User B's token used
- [x] 6.6 Test `/mytasks` for User A and User B, verify correct tasks returned for each user
- [x] 6.7 Restart bot and verify both users' tokens restored from encrypted file
- [x] 6.8 Test migration by copying a version 1.0 token file, starting bot, and verifying migration to version 2.0
- [x] 6.9 Verify log messages include user IDs for all token operations
- [x] 6.10 Test graceful shutdown and verify all users' tokens saved

## 7. Deployment Preparation

- [x] 7.1 Create deployment checklist: notify users to re-authenticate after upgrade
- [x] 7.2 Prepare rollback plan: revert commits, restore backup token file if needed
- [x] 7.3 Update `requirements.txt` with new dependencies (`httpx`)
- [ ] 7.4 Run `pip install -r requirements.txt` in production environment (dry run)
- [ ] 7.5 Create backup of `data/tokens.enc` before deployment
- [ ] 7.6 Deploy to production and monitor logs for errors
- [ ] 7.7 Verify multi-user functionality in production with test users
- [ ] 7.8 Update `openspec/changes/refactor-multi-tenancy-async-io/proposal.md` with deployment date and outcome

## Dependencies

- Tasks 2.x depend on completion of 1.x (handlers need updated TokenManager API)
- Tasks 3.x can be done in parallel with 1.x and 2.x (OutlookService async is independent)
- Tasks 4.x depend on completion of 1.x, 2.x, and 3.x (integration tests require all components)
- Tasks 5.x can be done in parallel with 4.x (documentation)
- Tasks 6.x depend on completion of 1.x through 4.x (manual testing requires working implementation)
- Tasks 7.x depend on completion of 1.x through 6.x (deployment requires tested code)

## Parallelizable Work

- **Phase 1 (Parallel):** 1.x (TokenManager) and 3.1-3.14 (OutlookService async conversion)
- **Phase 2 (Sequential):** 2.x (Handler updates) - must follow 1.x completion
- **Phase 3 (Parallel):** 3.15-3.19 (Handler async updates) and 4.x (Integration tests) - must follow 2.x completion
- **Phase 4 (Parallel):** 5.x (Documentation) and 6.x (Manual testing)
- **Phase 5 (Sequential):** 7.x (Deployment)
