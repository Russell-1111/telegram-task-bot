# llm-service Specification

## Purpose
This specification defines the requirements for LLM (Large Language Model) service integration, focusing on asynchronous, non-blocking inference operations for natural language understanding in the Telegram Task Bot.

## Requirements

### Requirement: Non-Blocking LLM Inference
The system SHALL perform LLM inference operations asynchronously without blocking the main asyncio event loop, enabling concurrent request handling across multiple users.

#### Scenario: Concurrent user requests during LLM inference
- **WHEN** User A sends a message requiring LLM analysis (e.g., "Buy groceries tomorrow")
- **AND** User B sends a `/start` command while User A's LLM request is in progress
- **THEN** the bot SHALL respond to User B's `/start` command immediately
- **AND** User A's LLM inference SHALL continue executing in a background thread
- **AND** User A SHALL receive their task creation confirmation once LLM analysis completes
- **AND** no user SHALL experience delays due to another user's LLM request

#### Scenario: Async LLM service method invocation
- **WHEN** a message handler calls `llm_service.analyze_task_request(user_message, current_date, last_task_context)`
- **THEN** the method SHALL be an async coroutine (declared with `async def`)
- **AND** the caller SHALL use `await` to invoke the method
- **AND** the blocking `self.model.generate_content(prompt)` call SHALL be wrapped in `asyncio.to_thread(...)`
- **AND** the method SHALL return a `TaskIntent` object asynchronously

#### Scenario: Thread pool execution for blocking LLM call
- **WHEN** `analyze_task_request` executes the LLM inference
- **THEN** the system SHALL use `await asyncio.to_thread(self.model.generate_content, prompt)` to offload the blocking call
- **AND** the LLM call SHALL execute in a separate thread from the default thread pool executor
- **AND** the asyncio event loop SHALL remain free to handle other requests
- **AND** the result SHALL be returned to the caller once inference completes

#### Scenario: Error handling preserves async behavior
- **WHEN** LLM inference fails with an exception (e.g., network error, API rate limit)
- **THEN** the exception SHALL be caught within the async `analyze_task_request` method
- **AND** a fallback `TaskIntent` SHALL be returned asynchronously
- **AND** the error SHALL be logged with appropriate context
- **AND** the event loop SHALL not be blocked by error handling

#### Scenario: Message handler awaits LLM analysis
- **WHEN** the `echo` function in `message_handlers.py` calls LLM service
- **THEN** the call SHALL use `task_intent = await llm_service.analyze_task_request(...)`
- **AND** the `echo` function SHALL already be declared as `async def` (no signature change needed)
- **AND** the function SHALL wait for the LLM result before proceeding with task creation
- **AND** no blocking calls SHALL occur in the handler code path

### Requirement: API Consistency with OutlookService Async Pattern
The LLMService SHALL follow the same asynchronous I/O pattern established by OutlookService for blocking external API calls.

#### Scenario: Consistent asyncio.to_thread usage pattern
- **WHEN** comparing LLMService and OutlookService implementations
- **THEN** both SHALL use `await asyncio.to_thread(blocking_function, *args)` for blocking external API calls
- **AND** both SHALL declare service methods as `async def`
- **AND** both SHALL return results asynchronously after I/O completes
- **AND** the codebase SHALL maintain a uniform async pattern across all service layers

#### Scenario: Documentation consistency
- **WHEN** reviewing service class docstrings
- **THEN** LLMService docstring SHALL note "All methods are async and use asyncio.to_thread to wrap blocking operations"
- **AND** the pattern SHALL match OutlookService documentation
- **AND** examples SHALL demonstrate async/await usage

### Requirement: Backward Compatibility for Internal API
The refactored LLMService SHALL maintain the same method signature (parameters and return type) except for the async declaration, minimizing breaking changes.

#### Scenario: Method signature preservation
- **WHEN** `analyze_task_request` is refactored to async
- **THEN** the method SHALL accept the same parameters: `user_message: str`, `current_date: datetime`, `last_task_context: Optional[Dict[str, Any]]`
- **AND** the method SHALL return the same `TaskIntent` dataclass
- **AND** the only API change SHALL be the requirement to use `await` when calling
- **AND** no parameter renaming or type changes SHALL occur

#### Scenario: Return value consistency
- **WHEN** the async `analyze_task_request` completes
- **THEN** it SHALL return a `TaskIntent` object with the same structure as before
- **AND** fallback behavior SHALL produce the same fallback `TaskIntent` format
- **AND** no changes to `TaskIntent` dataclass definition SHALL be required
- **AND** downstream code processing `TaskIntent` SHALL not require updates

#### Scenario: Single caller update required
- **WHEN** reviewing code that calls `llm_service.analyze_task_request`
- **THEN** only `src/handlers/message_handlers.py` SHALL require updates
- **AND** the update SHALL be limited to adding `await` before the method call
- **AND** no other handlers or modules SHALL need modifications
- **AND** the change SHALL be localized to minimize risk
