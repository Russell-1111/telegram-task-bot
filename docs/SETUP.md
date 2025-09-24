# Setup Guide

## Prerequisites

### 1. Python Environment
- **Python Version**: 3.8 or higher
- **Package Manager**: pip

### 2. API Keys Required

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create new bot with `/newbot`
3. Save the provided token

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Save for environment configuration

#### Microsoft Azure App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations"
3. Create new registration:
   - **Name**: Telegram Task Bot
   - **Account types**: Personal Microsoft accounts only
   - **Redirect URI**: Not required for device flow
4. Note the **Client ID** and **Tenant ID**
5. Configure API permissions:
   - Microsoft Graph → Delegated permissions → Tasks.ReadWrite

## Installation Steps

### 1. Project Setup
```bash
# Clone or download the project
cd telegram_task_bot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Set environment variables
set GEMINI_API_KEY=your_gemini_api_key_here

# Or create config file
copy config\config_template.py config\config.py
# Edit config.py with your actual values
```

### 3. Verify Installation
```bash
# Test bot startup
python src\bot.py
```

## Configuration Options

### Environment Variables
- `GEMINI_API_KEY` - Required for AI processing
- `TELEGRAM_BOT_TOKEN` - Can be set in code or environment

### Bot Settings
Edit values in `src\bot.py`:
- `TELEGRAM_BOT_TOKEN` - Your bot token
- `CLIENT_ID` - Azure client ID
- `AUTHORITY` - Azure authority URL

### Timezone Configuration
The bot is configured for Malaysia timezone (`Asia/Kuala_Lumpur`). To change:
1. Edit `MALAYSIA_TZ` in `src\bot.py`
2. Update timezone references in date formatting functions

## First Run

### 1. Start the Bot
```bash
# Using the start script
start-bot.bat

# Or directly
python src\bot.py
```

### 2. Connect to Telegram
1. Open Telegram
2. Search for your bot by username
3. Send `/start` command

### 3. Connect to Outlook
1. Send `/connectoutlook` command
2. Follow the device code authentication flow
3. Sign in with your Microsoft account

### 4. Test Task Creation
Send a message like: "Remind me to buy groceries tomorrow"

## Troubleshooting

### Common Issues

#### Bot doesn't respond
- Check `GEMINI_API_KEY` is set correctly
- Verify bot token is valid
- Ensure internet connection

#### Outlook connection fails
- Verify Azure app registration
- Check Microsoft account permissions
- Ensure Tasks.ReadWrite permission granted

#### "409 Conflict" errors
- Only run one bot instance at a time
- Use `scripts\git-revert.bat` if needed
- Check for orphaned processes

### Logs and Debugging
- Bot logs appear in console
- Error details logged for troubleshooting
- Use `INFO` log level for detailed output

## Security Considerations

### API Keys
- Never commit API keys to version control
- Use environment variables or config files
- Keep config files in `.gitignore`

### Bot Token
- Treat as password - keep secret
- Regenerate if compromised
- Use environment variables in production

### Microsoft Authentication
- Tokens stored in memory only
- Re-authentication required per session
- No persistent token storage