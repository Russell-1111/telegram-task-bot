# 🤖 Telegram Task Bot

An intelligent Telegram bot that integrates with Microsoft Outlook to manage tasks using AI-powered natural language processing.

## ✨ Features

- **🧠 AI-Powered Intent Detection**: Uses Google Gemini AI to understand user requests
- **📅 Task Management**: Create and update tasks in Microsoft Outlook
- **🇲🇾 Malaysia Timezone Support**: All dates handled in Asia/Kuala_Lumpur timezone
- **📝 Smart Summary Validation**: Enforces 3-12 word task summaries
- **🔄 Due Date Updates**: Modify task due dates with natural language
- **🔒 Conflict Prevention**: Single-instance protection with lock files
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
│   ├── bot.py             # Main bot application
│   ├── outlook_api.py     # Microsoft Graph API integration
│   └── task_cleanup.py    # Task cleanup utilities
├── scripts/               # Helper scripts
│   ├── git-save.bat      # Quick Git save
│   ├── git-revert.bat    # Revert to stable version
│   ├── git-history.bat   # View commit history
│   └── git-status.bat    # Git status overview
├── docs/                  # Documentation
├── config/               # Configuration files
├── .venv/               # Virtual environment
└── .git/                # Git repository
```

## 🔧 Usage

### Bot Commands
- `/start` - Start the bot
- `/connectoutlook` - Connect to Microsoft Outlook

### Natural Language Examples
- **Create Tasks**: "Remind me to buy groceries tomorrow"
- **Update Due Dates**: "Change due date to Friday"
- **Task Examples**: "Submit report by December 1st"

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
| Due Date Updates | ✅ | Modify task due dates dynamically |
| AI Intent Detection | ✅ | Gemini AI powered request analysis |
| Malaysia Timezone | ✅ | Proper timezone handling |
| Word Validation | ✅ | 3-12 word summary enforcement |
| Conflict Prevention | ✅ | Single instance protection |

## 🐛 Troubleshooting

- **409 Conflict Error**: Use `scripts\git-revert.bat` to stop multiple instances
- **Authentication Issues**: Reconnect using `/connectoutlook`
- **Invalid Summaries**: Bot automatically generates fallback summaries

## 📝 License

This project is for educational/personal use.

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome!