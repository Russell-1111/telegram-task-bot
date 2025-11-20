# 🤖 Telegram Task Bot

An intelligent Telegram bot that integrates with Microsoft Outlook to manage tasks using AI-powered natural language processing.

## ✨ Features

- **🧠 AI-Powered Intent Detection**: Uses Google Gemini AI to understand user requests
- **📅 Task Management**: Create, view, and update tasks in Microsoft Outlook
- **📋 Task Viewing**: Display uncompleted tasks with `/mytasks` command (Phase 2)
- **👥 Multi-User Support**: Independent token storage and session management for multiple concurrent users
- **⚡ Async Architecture**: Non-blocking I/O operations for improved responsiveness and scalability
- **🇲🇾 Malaysia Timezone Support**: All dates handled in Asia/Kuala_Lumpur timezone (UTC+8)
- **📝 Smart Summary Validation**: Enforces 3-12 word task summaries with auto-fallback
- **🔄 Due Date Updates**: Modify task due dates with natural language
- **🔒 Conflict Prevention**: Single-instance protection with lock files
- **🏗️ Clean Architecture**: Service layer pattern with OutlookService, StateManager, TokenManager (Phase 3)
- **⏱️ Rate Limiting**: 1 request/minute for `/mytasks` to prevent API spam
- **💪 Motivational Messages**: Dynamic encouragement based on task count and overdue status
- **📊 Version Control**: Git integration with helper scripts
- **🔐 Secure Token Storage**: Encrypted multi-user token persistence with automatic migration

## 🚀 Quick Start

### Prerequisites

#### System Requirements
- **Operating System**: Windows 10+, Linux, macOS
- **Python**: 3.8 or higher
- **Network**: Internet connection required
- **Accounts**: 
  - Microsoft account (for Outlook integration)
  - Telegram account
  - Google account (for Gemini API)

#### Required API Keys
- **Telegram Bot Token** - From [@BotFather](https://t.me/botfather)
- **Google Gemini API Key** - From [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Microsoft Azure App Registration** - Client ID from [Azure Portal](https://portal.azure.com)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telegram_task_bot
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install python-telegram-bot google-generativeai msal pytz requests
   ```

4. **Configure environment variables**
   
   **Option A: Using the setup script (Recommended)**
   ```powershell
   # 1. Edit .env file and add your API keys
   notepad .env
   
   # 2. Run the setup script
   .\setup-env.ps1
   
   # 3. Activate virtual environment
   .\.venv\Scripts\Activate.ps1
   
   # 4. Start the bot
   python src\bot.py
   ```
   
   **Option B: Manual environment variables**
   ```powershell
   $env:TELEGRAM_BOT_TOKEN="your_token_here"
   $env:GEMINI_API_KEY="your_key_here"
   $env:MS_CLIENT_ID="your_client_id_here"
   ```

5. **Get your API keys**
   - **Telegram Bot Token**: Talk to [@BotFather](https://t.me/botfather) on Telegram
   - **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - **Microsoft Client ID**: Create app in [Azure Portal](https://portal.azure.com) → App Registrations

6. **Run the bot**
   ```bash
   python src\bot.py
   ```

## 📁 Project Structure

```
telegram_task_bot/
├── src/                    # Source code
│   ├── bot.py             # Main bot application (49 lines - simplified!)
│   ├── outlook_api.py     # Microsoft Graph API (legacy module)
│   ├── task_cleanup.py    # Task cleanup utilities (refactored)
│   ├── config/            # Configuration management (Phase 1)
│   │   ├── __init__.py
│   │   └── settings.py    # Centralized settings loader
│   ├── services/          # Service layer (Phase 2-3)
│   │   ├── __init__.py
│   │   ├── llm_service.py        # Gemini AI integration
│   │   └── outlook_service.py    # Outlook API wrapper
│   ├── handlers/          # Telegram handlers (Phase 2)
│   │   ├── __init__.py
│   │   ├── command_handlers.py   # /start, /connectoutlook, /mytasks
│   │   └── message_handlers.py   # Natural language processing
│   ├── formatters/        # Display formatting (Phase 2)
│   │   ├── __init__.py
│   │   ├── task_formatter.py     # Task display with emojis
│   │   └── date_formatter.py     # Date validation/formatting
│   ├── validators/        # Input validation (Phase 1)
│   │   ├── __init__.py
│   │   └── task_validator.py     # Task summary validation
│   └── utils/             # Utilities (Phase 1 & 3)
│       ├── __init__.py
│       ├── lock_manager.py       # Single-instance protection
│       ├── state_manager.py      # User state management
│       └── token_manager.py      # Access token lifecycle
├── scripts/               # Helper scripts
│   ├── git-save.bat      # Quick Git save
│   ├── git-revert.bat    # Revert to stable version
│   ├── git-history.bat   # View commit history
│   └── git-status.bat    # Git status overview
├── docs/                  # Documentation
│   ├── API.md                    # API reference
│   ├── SETUP.md                  # Installation guide
│   ├── ARCHITECTURE-REVIEW.md    # Architecture analysis
│   ├── PHASE1-SUMMARY.md        # Phase 1 refactoring metrics
│   ├── PHASE2-SUMMARY.md        # Phase 2 refactoring metrics
│   └── PHASE3-SUMMARY.md        # Phase 3 refactoring metrics
├── config/               # Configuration templates
│   └── config_template.py
├── .venv/               # Virtual environment
└── .git/                # Git repository
```

## 🔧 Usage

### Bot Commands
- `/start` - Start the bot and see welcome message
- `/connectoutlook` - Connect to Microsoft Outlook account
- `/mytasks` - View your uncompleted tasks with motivational messages ✨

### Natural Language Examples
- **Create Tasks**: "Remind me to buy groceries tomorrow"
- **Update Due Dates**: "Change due date to Friday"
- **Task Examples**: "Submit report by December 1st"
- **Task Viewing**: Use `/mytasks` to see all uncompleted tasks with due dates

## ⚙️ Configuration

### Environment Variables Reference

The bot requires the following environment variables (stored in `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | - | Your Telegram bot token from [@BotFather](https://t.me/botfather) |
| `GEMINI_API_KEY` | ✅ Yes | - | Google Gemini AI API key for natural language processing |
| `MS_CLIENT_ID` | ✅ Yes | - | Azure app registration client ID for Outlook integration |
| `MS_TENANT_ID` | ⚠️ Optional | `common` | Azure tenant ID (use "common" for personal accounts) |
| `LOG_LEVEL` | ⚠️ Optional | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `MIN_TASK_WORDS` | ⚠️ Optional | `3` | Minimum words for task summary validation |
| `MAX_TASK_WORDS` | ⚠️ Optional | `12` | Maximum words for task summary validation |

### State Persistence Configuration

The bot now supports **persistent state management** to preserve user sessions and authentication tokens across restarts:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STATE_ENCRYPTION_KEY` | ⚠️ Optional | Auto-generated | Base64-encoded 32-byte key for token encryption (Fernet) |
| `DATA_DIR` | ⚠️ Optional | `data` | Directory path for state files |
| `ENABLE_PERSISTENCE` | ⚠️ Optional | `true` | Enable/disable persistence (`true` or `false`) |
| `BACKUP_RETENTION_COUNT` | ⚠️ Optional | `3` | Number of backup files to keep (1-10) |
| `AUTO_SAVE_INTERVAL_SECONDS` | ⚠️ Optional | `300` | Auto-save interval in seconds (0 = disable, 5 minutes default) |

**Key Features:**
- **Encrypted Tokens**: Microsoft Graph tokens encrypted at rest using Fernet (AES-128-CBC + HMAC)
- **Auto-Save**: Background thread saves state every 5 minutes (configurable)
- **Graceful Degradation**: Falls back to in-memory storage if persistence fails
- **Automatic Backups**: Rotating backups with configurable retention
- **Secure Permissions**: Files created with restrictive permissions (owner-only access)

**Quick Setup:**
```powershell
# Option 1: Auto-generate encryption key (simplest)
# Just enable persistence, key will be auto-generated on first run
$env:ENABLE_PERSISTENCE="true"

# Option 2: Manual key generation (recommended for production)
$env:STATE_ENCRYPTION_KEY="<your-base64-key-here>"
$env:ENABLE_PERSISTENCE="true"
$env:DATA_DIR="data"
```

**Generate Encryption Key:**
```powershell
# Using Python to generate a secure key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

⚠️ **Important**: Store your `STATE_ENCRYPTION_KEY` securely! Losing it means losing access to all encrypted tokens.

For detailed persistence documentation, see [`docs/PERSISTENCE-GUIDE.md`](docs/PERSISTENCE-GUIDE.md).

### Setup Instructions

**Option A: Using .env file (Recommended)**
1. Edit the `.env` file in the project root
2. Add your API keys (file is protected by `.gitignore`)
3. Run `.\setup-env.ps1` to load variables
4. Start the bot with `.\start-bot.bat`

**Option B: Manual environment variables (PowerShell)**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_token_here"
$env:GEMINI_API_KEY="your_key_here"
$env:MS_CLIENT_ID="your_client_id_here"
```

### Timezone Configuration
The bot is configured for **Malaysia timezone** (`Asia/Kuala_Lumpur` - UTC+8).  
To change the timezone, edit `src/config/settings.py`:
```python
timezone: pytz.tzinfo.BaseTzInfo = field(default_factory=lambda: pytz.timezone('Your/Timezone'))
```

## 🛠️ Development

### Dependencies

The project uses the following key dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `python-telegram-bot` | ≥21.0.0 | Telegram Bot API framework for handling commands and messages |
| `google-generativeai` | ≥0.3.0 | Google Gemini AI for natural language understanding and intent detection |
| `msal` | ≥1.20.0 | Microsoft Authentication Library for OAuth device code flow |
| `requests` | ≥2.28.0 | HTTP library for Microsoft Graph API calls |
| `pytz` | ≥2023.3 | Timezone handling (Malaysia UTC+8 support) |

#### Optional Development Dependencies
```python
# Add to requirements.txt for development
pytest>=7.0.0      # Unit testing framework
black>=23.0.0      # Code formatting
flake8>=6.0.0      # Code linting
```

### Git Workflow
Use the provided helper scripts:
```bash
scripts\git-status.bat           # Check current status
scripts\git-save.bat "message"   # Save changes with commit message
scripts\git-revert.bat           # Revert to stable version
scripts\git-history.bat          # View commit history
```

### Version Control
The project maintains a stable branch (`stable-v1.0`) for reliable rollbacks.

### Project Standards
- **Architecture**: Service layer pattern (Phase 3 complete)
- **Code Coverage**: Aim for 80%+ test coverage
- **Documentation**: Inline docstrings + external docs
- **Logging**: Comprehensive logging with configurable levels
- **Error Handling**: Graceful degradation with user-friendly messages

## 📊 Features Overview

| Feature | Status | Description |
|---------|--------|-------------|
| Task Creation | ✅ | Create Outlook tasks via natural language |
| Task Viewing | ✅ | View uncompleted tasks with `/mytasks` command |
| Due Date Updates | ✅ | Modify task due dates dynamically |
| AI Intent Detection | ✅ | Gemini AI powered request analysis |
| Malaysia Timezone | ✅ | Proper timezone handling (UTC+8) |
| Word Validation | ✅ | 3-12 word summary enforcement with fallback |
| Conflict Prevention | ✅ | Single instance protection with lock files |
| Service Layer | ✅ | Clean architecture (OutlookService, StateManager, TokenManager) |
| Rate Limiting | ✅ | 1 request/minute for `/mytasks` to prevent spam |
| Motivational Messages | ✅ | Dynamic encouragement based on task count |
| State Management | ✅ | Centralized user state (zero global variables) |
| **Persistent State** | ✅ | **Encrypted token storage, auto-save, session recovery** |

## 🏗️ Architecture

This bot follows a **clean service layer architecture** implemented across 3 refactoring phases:

### **Phase 1: Foundation** (Configuration, Lock Manager, Validators)
- ✅ Centralized configuration management
- ✅ Single-instance protection
- ✅ Input validation layer

### **Phase 2: Structural Improvements** (Services, Handlers, Formatters)
- ✅ LLM service for AI integration
- ✅ Separated command and message handlers
- ✅ Task and date formatters
- ✅ Reduced `bot.py` from 772 to 49 lines (93.7% reduction!)

### **Phase 3: Service Layer Refinement** (OutlookService, StateManager, TokenManager)
- ✅ OutlookService wraps Microsoft Graph API
- ✅ UserStateManager manages user task state
- ✅ TokenManager handles access token lifecycle
- ✅ **Zero global variables** - all state properly managed

**Architecture Grade:** A- (up from D before refactoring)  
**Coupling:** 2/10 (Excellent)  
**Cohesion:** 9/10 (Excellent)  
**Testability:** +98%

See [`docs/PHASE1-SUMMARY.md`](docs/PHASE1-SUMMARY.md), [`docs/PHASE2-SUMMARY.md`](docs/PHASE2-SUMMARY.md), and [`docs/PHASE3-SUMMARY.md`](docs/PHASE3-SUMMARY.md) for detailed metrics.

## 🔒 Security

### API Key Protection
- ✅ **`.env` file** is excluded from git via `.gitignore`
- ✅ **Never commit** API keys or tokens to version control
- ✅ **Token storage** uses encrypted persistence (Fernet AES-128-CBC + HMAC)
- ✅ **Encryption keys** stored separately from encrypted data
- ✅ **File permissions** restricted to owner-only (0600 Unix, user-only ACL Windows)
- ✅ **Setup script** displays masked values for security
- ⚠️ **Keep `.env` file** permissions restricted (read-only for your user)
- ⚠️ **Backup encryption key** (`STATE_ENCRYPTION_KEY`) securely
- ⚠️ **Regenerate keys immediately** if accidentally exposed

### Persistence Security
- **Encryption at Rest**: Microsoft Graph tokens encrypted using Fernet (symmetric encryption)
- **Key Management**: Encryption key stored in environment variable (separate from data)
- **Automatic Backups**: 3 rotating backups with timestamp-based naming
- **Secure Permissions**: Data files created with restrictive access (owner-only)
- **Graceful Degradation**: Falls back to in-memory if persistence fails

### Best Practices
- **Development**: Use `.env` file for local development
- **Production**: Use system environment variables or secrets management
- **Never hardcode** API keys in source code
- **Rotate keys** periodically for enhanced security
- **Monitor usage** in Azure Portal and Google AI Studio for suspicious activity

### What to Do if Keys are Compromised
1. **Telegram Bot Token**: Regenerate via [@BotFather](https://t.me/botfather) → `/revoke`
2. **Gemini API Key**: Delete and create new key in [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **Azure Client ID**: Disable app registration in [Azure Portal](https://portal.azure.com)
4. **Update** all instances with new keys
5. **Review** access logs for unauthorized usage

## ⚠️ Known Limitations

### Current Constraints
- **Single-user authentication**: TokenManager stores one token globally (not per-user)
  - *Workaround*: For multi-user support, implement per-user token storage
- **Session-based tokens**: Access tokens expire after ~1 hour
  - *Workaround*: Tokens are now saved persistently and restored on restart
  - *Future*: Automatic token refresh mechanism planned
- **Hardcoded timezone**: All dates use Malaysia timezone (UTC+8)
  - *Workaround*: Modify `src/config/settings.py` for different timezone
- **Rate limiting**: `/mytasks` command limited to 1 request/minute per user
  - *Purpose*: Prevent Microsoft Graph API spam
- **Task limit**: Displays maximum 10 tasks in `/mytasks` view
  - *Workaround*: Use filters or pagination for more tasks

### Microsoft Graph API Limitations
- **Authentication**: Device code flow requires manual user interaction
- **Task operations**: Limited to default task list
- **API quotas**: Subject to Microsoft Graph API throttling limits
- **Token expiry**: Standard OAuth tokens expire after 60 minutes

## 🧪 Testing

### Quick Testing
```bash
# Run the bot
.\start-bot.bat

# Manual testing in Telegram
# 1. Send /start
# 2. Send /connectoutlook
# 3. Create task: "Buy groceries tomorrow"
# 4. Send /mytasks
```

### Automated Testing
```bash
# Run full test suite
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_api_documentation.py
python -m pytest tests/test_documentation_examples.py
```

### Testing Checklist
- ✅ Bot startup without errors
- ✅ `/start` command shows welcome message
- ✅ `/connectoutlook` initiates device code flow
- ✅ Task creation with natural language
- ✅ `/mytasks` displays tasks with formatting
- ✅ Rate limiting works (1 req/min)
- ✅ Error handling for invalid inputs
- ✅ Lock file prevents multiple instances

For comprehensive testing instructions, see [TESTING-GUIDE.md](TESTING-GUIDE.md).

## 📚 Documentation

- **[API Reference](docs/API.md)** - Complete API documentation for all services, utilities, and commands
- **[Code Examples](docs/EXAMPLES.md)** - Practical usage patterns, integration examples, and common recipes
- **[Testing Guide](TESTING-GUIDE.md)** - Testing instructions and module reference
- **[Architecture Review](docs/ARCHITECTURE-REVIEW.md)** - Detailed architecture analysis and design decisions
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration instructions
- **[Phase 1 Summary](docs/PHASE1-SUMMARY.md)** - Configuration, Lock Manager, Validators
- **[Phase 2 Summary](docs/PHASE2-SUMMARY.md)** - Services, Handlers, Formatters
- **[Phase 3 Summary](docs/PHASE3-SUMMARY.md)** - Service Layer Refinement

## 📝 Changelog

### v1.3.0 (October 2025) - Phase 3: Service Layer Refinement
- ✅ Added `OutlookService` for Microsoft Graph API abstraction
- ✅ Implemented `UserStateManager` for centralized state management
- ✅ Created `TokenManager` for access token lifecycle
- ✅ **Eliminated all global variables** (100% removal)
- ✅ Architecture grade improved to A- (from D)
- ✅ Coupling reduced to 2/10 (from 8/10)
- ✅ Cohesion improved to 9/10 (from 2/10)
- ✅ Testability increased by 98%

### v1.2.0 (October 2025) - Phase 2: Structural Improvements
- ✅ Separated command and message handlers
- ✅ Added `LLMService` for AI integration
- ✅ Created `TaskFormatter` and `DateFormatter` modules
- ✅ Reduced `bot.py` from 772 to 49 lines (93.7% reduction)
- ✅ Implemented `/mytasks` command with rate limiting
- ✅ Added motivational messages based on task count

### v1.1.0 (October 2025) - Phase 1: Foundation
- ✅ Centralized configuration management (`settings.py`)
- ✅ Single-instance protection with `BotLockManager`
- ✅ Task summary validation (3-12 words) with auto-fallback
- ✅ Input validation layer for data integrity

### v1.0.0 (October 2025) - Initial Release
- ✅ Basic task creation with AI-powered intent detection
- ✅ Microsoft Outlook integration via Graph API
- ✅ Natural language processing with Google Gemini
- ✅ Malaysia timezone support (UTC+8)
- ✅ Due date updates and task management

## 🐛 Troubleshooting

### Common Issues

#### Bot doesn't respond to commands
- **Check** `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- **Verify** bot token is valid with [@BotFather](https://t.me/botfather)
- **Ensure** internet connection is active
- **Review** console logs for error messages
- **Restart** bot after configuration changes

#### Outlook connection fails
- **Verify** Azure app registration is configured correctly
- **Check** Microsoft account has permissions for Tasks
- **Ensure** `Tasks.ReadWrite` permission is granted in Azure Portal
- **Try** using "common" as `MS_TENANT_ID` for personal accounts
- **Wait** for device code to expire (default: 15 minutes), then retry

#### "409 Conflict" errors
- **Stop** all running bot instances
- **Delete** `bot.lock` file manually if needed
- **Use** `scripts\git-revert.bat` to clean up
- **Check** Task Manager for orphaned Python processes
- **Restart** with `.\start-bot.bat`

#### Token expired / Authentication issues
- **Reconnect** using `/connectoutlook` command
- **Note**: Tokens expire after ~1 hour (Microsoft Graph limitation)
- **Check** token age with error logs
- **Future**: Automatic refresh planned

#### Invalid task summaries
- **Bot automatically** generates fallback summaries if validation fails
- **Ensure** summaries are 3-12 words (configurable in `.env`)
- **Example**: "Buy" → Auto-fixed to "Complete important task"

#### Rate limiting message appears
- **Wait** the specified cooldown period (60 seconds for `/mytasks`)
- **Purpose**: Prevents overwhelming Microsoft Graph API
- **Current limit**: 1 request per minute per user

### Debug Mode

Enable detailed logging:
```powershell
# In .env file
LOG_LEVEL=DEBUG

# Restart bot
.\start-bot.bat
```

### Getting Help
- 📖 Check [SETUP.md](docs/SETUP.md) for detailed configuration
- 🔍 Review [TESTING-GUIDE.md](TESTING-GUIDE.md) for test procedures
- 🐛 Open an issue on GitHub with:
  - Error message and stack trace
  - Bot configuration (without sensitive keys)
  - Steps to reproduce
  - Expected vs actual behavior

## ❓ Frequently Asked Questions (FAQ)

### General Questions

**Q: Can multiple users use the same bot instance?**  
A: Currently, the bot stores a single access token globally (via `TokenManager`). For multi-user support, you'd need to implement per-user token storage. This is a known limitation documented above.

**Q: How long do access tokens last?**  
A: Microsoft Graph access tokens typically expire after 60 minutes. Users must re-authenticate using `/connectoutlook` when tokens expire. Automatic token refresh is planned for a future release.

**Q: Can I use this bot with Google Tasks or Todoist?**  
A: Currently, the bot only supports Microsoft Outlook Tasks via Graph API. Support for other task management services could be added by creating additional service layer classes.

**Q: Is there a way to backup my tasks?**  
A: The bot doesn't store tasks locally - all tasks are managed by Microsoft Outlook. Your tasks are backed up by Microsoft's cloud infrastructure.

### Technical Questions

**Q: Why is the timezone hardcoded to Malaysia (UTC+8)?**  
A: The original implementation was for a user in Malaysia. You can change the timezone by editing `src/config/settings.py` and modifying the `timezone` setting.

**Q: Can I run this bot on a server (24/7)?**  
A: Yes! Deploy to any server with Python 3.8+. Use system environment variables instead of `.env` file for production. Consider implementing automatic token refresh for unattended operation.

**Q: How do I add support for recurring tasks?**  
A: Microsoft Graph API supports recurring tasks. You'd need to extend `OutlookService.create_task()` to include recurrence patterns in the payload. See Microsoft Graph API documentation for recurrence schema.

**Q: Does this bot support task categories or tags?**  
A: Not currently, but Microsoft Graph API supports categories. This could be added by extending the `create_task` and `update_task` methods in `OutlookService`.

**Q: Can I customize the motivational messages?**  
A: Yes! Edit `src/formatters/task_formatter.py` and modify the `get_motivational_message()` function to customize messages based on task count.

### Troubleshooting Questions

**Q: I keep getting "409 Conflict" errors. What's wrong?**  
A: This means multiple bot instances are trying to run simultaneously. The bot uses a lock file to prevent this. Stop all instances, delete `bot.lock` manually, and restart with `.\start-bot.bat`.

**Q: The bot doesn't understand my natural language requests. Why?**  
A: The bot uses Google Gemini AI for natural language processing. Ensure your `GEMINI_API_KEY` is valid and you have API quota remaining. Try being more explicit, e.g., "Create task: Buy milk, due: tomorrow".

**Q: My task summaries keep getting auto-corrected. Can I disable this?**  
A: The bot enforces 3-12 word task summaries by default. You can adjust these limits in `.env` by setting `MIN_TASK_WORDS` and `MAX_TASK_WORDS`. The auto-fallback ensures tasks are always created even with invalid summaries.

**Q: Can I see deleted or completed tasks?**  
A: Currently, `/mytasks` only shows uncompleted tasks. You can extend `OutlookService` to add a method for fetching completed tasks or use `get_all_tasks()` directly.

### Development Questions

**Q: How do I run the tests?**  
A: Run `python -m pytest tests/ -v` for the full test suite, or test specific modules with `python -m pytest tests/test_<module>.py`.

**Q: Where should I add new features?**  
A: Follow the service layer architecture:
- API interactions → `src/services/outlook_service.py`
- AI processing → `src/services/llm_service.py`
- New commands → `src/handlers/command_handlers.py`
- Message processing → `src/handlers/message_handlers.py`
- Formatting → `src/formatters/`
- Validation → `src/validators/`

**Q: How do I debug API calls?**  
A: Set `LOG_LEVEL=DEBUG` in `.env` and restart the bot. This will log all API requests, responses, and errors to the console.

---

## 📝 License

This project is for educational/personal use. See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

This is a personal educational project, but contributions are welcome!

### How to Contribute

#### Reporting Bugs
1. **Check** existing issues to avoid duplicates
2. **Open** a new issue with:
   - Clear, descriptive title
   - Detailed description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)
   - Error logs (without sensitive data)

#### Suggesting Features
1. **Open** an issue with the "enhancement" label
2. **Describe** the feature and its benefits
3. **Explain** use cases and examples
4. **Discuss** implementation approach if possible

#### Submitting Pull Requests
1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Make** your changes following the code style
4. **Test** thoroughly with existing test suite
5. **Commit** with descriptive messages:
   ```bash
   git commit -m 'Add AmazingFeature: Description of changes'
   ```
6. **Push** to your branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
7. **Open** a Pull Request with:
   - Clear description of changes
   - Related issue numbers
   - Screenshots/examples if applicable
   - Test results

### Code Style Guidelines
- Follow **PEP 8** for Python code
- Use **type hints** for function parameters and returns
- Write **docstrings** for all public functions and classes
- Add **comments** for complex logic
- Keep functions **small and focused** (single responsibility)
- Use **meaningful variable names**
- Include **error handling** for external API calls

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/telegram-task-bot.git
cd telegram-task-bot

# Set up development environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8

# Run tests
python -m pytest

# Format code
black src/

# Lint code
flake8 src/
```

### Areas for Contribution
- 🔄 Automatic token refresh mechanism
- 💾 Database integration for persistent state
- 🌍 Multi-timezone support
- 👥 Multi-user token management
- 📊 Advanced task analytics and reporting
- 🔔 Task reminder notifications
- 🎨 Custom task formatting options
- 🧪 Expanded test coverage
- 📖 Documentation improvements
- 🌐 Internationalization (i18n)

### Community Guidelines
- Be respectful and constructive
- Help others in discussions
- Follow the code of conduct
- Keep discussions on-topic
- Provide helpful feedback on PRs

Thank you for contributing! 🎉