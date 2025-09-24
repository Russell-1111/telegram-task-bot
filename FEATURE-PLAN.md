# Feature Development Plan

## Current Status
- **Date**: September 24, 2025
- **Branch**: feature/new-functionality
- **Base Version**: Master branch (stable checkpoint)

## Proposed Feature
**Feature Name**: My Tasks Display with Motivational Messaging

### Description
Add a `/mytasks` command that fetches and displays the user's current uncompleted Outlook tasks with motivational messages based on task count. This feature will help users stay organized and motivated by showing their pending tasks with encouraging messages.

### Requirements
- [ ] **Functional Requirements**
  - Fetch uncompleted tasks from user's Outlook task list
  - Display tasks in a clean, readable format with title, due date, and priority
  - Generate motivational messages based on task count and completion status
  - Limit display to maximum 10 tasks per message to avoid Telegram limits
  - Handle cases where user has no tasks (celebration message)

- [ ] **Technical Requirements**
  - Extend `outlook_api.py` with new `get_uncompleted_tasks()` function
  - Add `/mytasks` command handler to `bot.py`
  - Implement task formatting with Telegram markdown support
  - Create motivational message templates with dynamic placeholders
  - Add proper error handling for API failures and empty task lists
  - Implement rate limiting (1 request per minute per user)

### Implementation Plan

#### Phase 1: Analysis ✅
- [x] Review existing code architecture in `src/bot.py` (command handlers, echo function)
- [x] Analyze `src/outlook_api.py` current functions (create_outlook_task, update_task_due_date)
- [x] Identify files that need modification:
  - [x] `src/bot.py` - Add `/mytasks` command handler and motivational message logic
  - [x] `src/outlook_api.py` - Add `get_uncompleted_tasks()` function
  - [x] No changes needed to `src/task_cleanup.py`
- [x] Check for potential conflicts with existing features (no conflicts expected)

#### Phase 2: Development ✅
- [x] **Step 1**: Add `get_uncompleted_tasks()` function to `outlook_api.py`
  - [x] Use Microsoft Graph API endpoint: `/me/todo/lists/{listId}/tasks`
  - [x] Filter for tasks where `status != 'completed'`
  - [x] Include task title, due date, priority, and created date
  - [x] Handle pagination if user has many tasks
- [x] **Step 2**: Create task formatting function in `bot.py`
  - [x] Format tasks with Telegram markdown (📋 📅 ⚡ emojis)
  - [x] Handle missing due dates gracefully
  - [x] Limit to 10 tasks maximum per display
- [x] **Step 3**: Implement motivational message system
  - [x] Create array of motivational templates
  - [x] Add dynamic placeholders for task count, overdue count
  - [x] Randomize message selection
- [x] **Step 4**: Add `/mytasks` command handler
  - [x] Integrate with existing command structure
  - [x] Add error handling and user feedback
  - [x] Implement rate limiting

#### Phase 3: Testing ✅ 
- [x] **Unit Testing**: Test `get_uncompleted_tasks()` function with mock data
- [x] **Integration Testing**: Test full `/mytasks` command flow
- [x] **Edge Case Testing**: Empty task list, API failures, overdue tasks
- [x] **User Acceptance Testing**: Verify message formatting and motivational content

**Implementation Completed**: All functions successfully added and integrated. Bot imports and initializes correctly with no syntax errors.

#### Phase 4: Documentation
- [ ] Update README.md with new `/mytasks` command documentation
- [ ] Update `docs/API.md` with new Outlook API function
- [ ] Add inline code comments for new functions
- [ ] Create usage examples with sample outputs

### Rollback Plan
If something goes wrong:
1. Use `git checkout master` to return to stable version
2. Use `scripts/git-revert.bat` for emergency recovery
3. Current stable commit: `8f33347`

### Success Criteria ✅
- [x] `/mytasks` command successfully retrieves and displays uncompleted tasks
- [x] Tasks are formatted clearly with title, due date, and priority
- [x] Motivational messages display correctly based on task count
- [x] Rate limiting prevents API abuse (max 1 request per minute)
- [x] Graceful handling of empty task lists and API errors
- [x] No breaking changes to existing task creation/update functionality
- [x] All existing tests continue to pass
- [x] New feature integrates seamlessly with current bot commands

**Status**: 🎉 **FEATURE IMPLEMENTED SUCCESSFULLY** 🎉

### Expected Output Example
```
User: /mytasks
Bot: 📋 **Your Current Tasks** (5 remaining)

1. 📅 **Q4 Report Review** - Due Today ⚡ High Priority
2. 📅 **Team Meeting Prep** - Due Tomorrow
3. **Client Proposal Draft** - No due date
4. 📅 **Budget Planning** - Due Friday ⚡ High Priority
5. **Update Documentation** - No due date

💪 **You're doing great!** Just 5 tasks to go - you've got this! 🚀
```

### Notes
- **API Considerations**: Microsoft Graph API has rate limits - implement proper throttling
- **Message Length**: Telegram has 4096 character limit - truncate if needed
- **Time Zone**: Use existing Malaysia timezone (Asia/Kuala_Lumpur) for due date display
- **Error Messages**: Provide helpful feedback if Outlook API is unavailable
- **Future Enhancements**: Could add task filtering by priority, due date, or category

---
**Remember**: Commit frequently with descriptive messages during development!