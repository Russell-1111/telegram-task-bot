# Refactor LLMService to Use Non-Blocking Asynchronous I/O

## Why
The current implementation of `analyze_task_request` in `src/services/llm_service.py` makes a synchronous blocking call to `self.model.generate_content`, which blocks the main asyncio event loop for 2-10 seconds during LLM inference. This causes the bot to freeze and become unresponsive to all other users during the inference period, severely degrading user experience when multiple users interact with the bot concurrently.

## What Changes
- **LLMService refactor**: Convert `analyze_task_request` method from synchronous (`def`) to asynchronous (`async def`) and wrap the blocking `self.model.generate_content(prompt)` call using `await asyncio.to_thread(...)` to offload execution to a separate thread pool, preventing event loop blocking.

- **Message handler updates**: Update `src/handlers/message_handlers.py` to `await` the now-asynchronous `llm_service.analyze_task_request(...)` call.

- **API consistency**: Align `LLMService` with the existing async pattern established by `OutlookService`, which already uses `asyncio.to_thread` for blocking Graph API calls.

## Impact
- **Affected specs**: New `llm-service` capability specification
- **Affected code**: 
  - `src/services/llm_service.py` (LLMService class, analyze_task_request method)
  - `src/handlers/message_handlers.py` (echo function)
- **Performance**: Eliminates event loop blocking, allowing concurrent handling of /start, /mytasks, and other requests while waiting for LLM responses
- **API**: `LLMService.analyze_task_request` becomes an awaitable coroutine; all callers must use `await`
- **Breaking change**: No breaking changes for end users; internal API change only affects bot code
