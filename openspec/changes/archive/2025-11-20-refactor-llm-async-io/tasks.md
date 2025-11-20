## 1. Implementation

- [x] 1.1 Import `asyncio` module in `src/services/llm_service.py`
- [x] 1.2 Change `analyze_task_request` method signature from `def` to `async def` in `LLMService` class
- [x] 1.3 Wrap `self.model.generate_content(prompt)` call with `await asyncio.to_thread(...)` to offload blocking LLM inference to a thread
- [x] 1.4 Update `src/handlers/message_handlers.py` to `await` the `llm_service.analyze_task_request(...)` call in the `echo` function
- [x] 1.5 Update LLMService docstring to document async behavior and mention `asyncio.to_thread` usage pattern

## 2. Testing

- [x] 2.1 Write unit test for async `analyze_task_request` method mocking `asyncio.to_thread` and `generate_content`
- [x] 2.2 Write integration test simulating concurrent user requests (one LLM inference, one `/start` command) to verify non-blocking behavior
- [x] 2.3 Test error handling: verify exceptions during LLM inference are caught and fallback intent is returned asynchronously
- [x] 2.4 Test that existing synchronous LLM service unit tests (if any) are updated or replaced with async equivalents
- [x] 2.5 Run full test suite with `pytest` to ensure no regressions in message handling or task creation flows

## 3. Validation

- [x] 3.1 Manual test: Start bot, send a task creation message from User A, immediately send `/start` from User B, verify User B receives instant response
- [x] 3.2 Manual test: Send multiple task creation messages from different users concurrently, verify all are processed correctly without delays
- [x] 3.3 Check logs to confirm no "Blocking call in event loop" warnings or similar asyncio errors
- [x] 3.4 Verify LLM inference timing: ensure response times remain consistent (2-10 seconds for LLM, no additional overhead from async wrapper)
- [x] 3.5 Review code with `rg "def analyze_task_request"` to confirm method is declared as `async def` everywhere

## 4. Documentation

- [x] 4.1 Update API.md (or relevant docs) to note `LLMService.analyze_task_request` is now async and requires `await`
- [x] 4.2 Update ARCHITECTURE-REVIEW.md (if exists) to document async pattern consistency between LLMService and OutlookService
- [x] 4.3 Add inline code comments explaining `asyncio.to_thread` usage for future maintainers
- [x] 4.4 Update any developer guides or onboarding docs mentioning LLM service usage patterns
