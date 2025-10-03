# 🤖 Telegram Task Bot

An intelligent Telegram bot that integrates with Microsoft Outlook to manage tasks using AI-powered natural language processing.

## ✨ Features

- **🧠 AI-Powered Intent Detection**: Uses Google Gemini AI to understand user requests
- **📅 Task Management**: Create, view, and update tasks in Microsoft Outlook
- **📋 Task Viewing**: Display uncompleted tasks with `/mytasks` command (Phase 2)
- **🇲🇾 Malaysia Timezone Support**: All dates handled in Asia/Kuala_Lumpur timezone (UTC+8)
- **📝 Smart Summary Validation**: Enforces 3-12 word task summaries with auto-fallback
- **🔄 Due Date Updates**: Modify task due dates with natural language
- **🔒 Conflict Prevention**: Single-instance protection with lock files
- **🏗️ Clean Architecture**: Service layer pattern with OutlookService, StateManager, TokenManager (Phase 3)
- **⏱️ Rate Limiting**: 1 request/minute for `/mytasks` to prevent API spam
- **💪 Motivational Messages**: Dynamic encouragement based on task count and overdue status
- **📊 Version Control**: Git integration with helper scripts

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Google Gemini API Key
- Microsoft Azure App Registration

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
   ```bash
   set GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the bot**
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

The bot requires the following configuration:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `GEMINI_API_KEY` - Google Gemini API key
- Microsoft Azure app registration for Outlook integration

## 🛠️ Development

### Git Workflow
Use the provided helper scripts:
```bash
scripts\git-status.bat      # Check current status
scripts\git-save.bat "message"  # Save changes
scripts\git-revert.bat      # Revert to stable version
```

### Version Control
The project maintains a stable branch (`stable-v1.0`) for reliable rollbacks.

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

## � Documentation

- **[API Reference](docs/API.md)** - Complete API documentation for all services, utilities, and commands
- **[Code Examples](docs/EXAMPLES.md)** - Practical usage patterns, integration examples, and common recipes
- **[Testing Guide](TESTING-GUIDE.md)** - Testing instructions and module reference
- **[Architecture Review](docs/ARCHITECTURE-REVIEW.md)** - Detailed architecture analysis and design decisions
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration instructions

## �🐛 Troubleshooting

- **409 Conflict Error**: Use `scripts\git-revert.bat` to stop multiple instances
- **Authentication Issues**: Reconnect using `/connectoutlook`
- **Invalid Summaries**: Bot automatically generates fallback summaries

## 📝 License

This project is for educational/personal use.

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome!