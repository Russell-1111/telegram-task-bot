# API Documentation

## Bot Commands

### `/start`
Initializes the bot and sends a welcome message.

**Response**: Welcome message with basic instructions.

### `/connectoutlook`
Initiates Microsoft Outlook authentication flow.

**Response**: Device code authentication URL for Microsoft login.

## Natural Language Processing

The bot uses Google Gemini AI to process natural language and extract:

### Intent Detection
- `create_task` - User wants to create a new task
- `update_due_date` - User wants to modify existing task due date
- `unknown` - Request doesn't match known patterns

### Task Summary Rules
- **Minimum**: 3 words
- **Maximum**: 12 words
- **Validation**: Automatic fallback generation if invalid
- **Examples**: 
  - ✅ "Buy groceries and milk" (4 words)
  - ❌ "Buy groceries" (2 words - too short)

### Due Date Processing
- **Formats Supported**:
  - Relative: "tomorrow", "next Friday", "in 3 days"
  - Absolute: "December 1st", "2025-10-26"
  - Time expressions: "next week", "tonight"
- **Timezone**: All dates processed in Malaysia timezone (UTC+8)
- **Default Time**: 5:00 PM Malaysia time

## Microsoft Graph API Integration

### Authentication
- **Method**: Device Code Flow (MSAL)
- **Scopes**: Tasks.ReadWrite
- **Token Storage**: Memory (session-based)

### Task Operations

#### Create Task
- **Endpoint**: `/me/todo/lists/{listId}/tasks`
- **Method**: POST
- **Payload**:
  ```json
  {
    "title": "Task summary",
    "dueDateTime": {
      "dateTime": "2025-12-01T17:00:00.0000000",
      "timeZone": "Asia/Kuala_Lumpur"
    }
  }
  ```

#### Update Task Due Date
- **Endpoint**: `/me/todo/lists/{listId}/tasks/{taskId}`
- **Method**: PATCH
- **Features**: 
  - Automatic list discovery
  - URL encoding for task IDs
  - Task existence verification

## Error Handling

### Common Errors
- **409 Conflict**: Multiple bot instances
- **400 Bad Request**: Invalid API payload
- **401 Unauthorized**: Token expired
- **404 Not Found**: Task not found

### Recovery Mechanisms
- Automatic token refresh
- Fallback summary generation
- Graceful error messages to users
- Comprehensive logging