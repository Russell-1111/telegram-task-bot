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

### 2. Environment Configuration

**⭐ Recommended: Using .env file**

1. Open the `.env` file (already created in project root)
2. Fill in your API keys:
   ```env
   TELEGRAM_BOT_TOKEN=your_actual_telegram_token_here
   GEMINI_API_KEY=your_actual_gemini_key_here
   MS_CLIENT_ID=your_actual_microsoft_client_id_here
   MS_TENANT_ID=common  # or your specific tenant ID
   ```

3. Save the file (it's already protected by `.gitignore`)

**Alternative: Manual environment variables (PowerShell)**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_token_here"
$env:GEMINI_API_KEY="your_key_here"
$env:MS_CLIENT_ID="your_client_id_here"
```

### 3. Verify Installation
```bash
# Load environment and test bot startup
.\setup-env.ps1  # Loads variables from .env
python src\bot.py
```

## Configuration Options

### Environment Variables (Loaded from .env file)
- `TELEGRAM_BOT_TOKEN` - **Required** - Your Telegram bot token
- `GEMINI_API_KEY` - **Required** - Google Gemini API key for AI processing
- `MS_CLIENT_ID` - **Required** - Azure app registration client ID
- `MS_TENANT_ID` - **Optional** - Azure tenant ID (defaults to "common")
- `LOG_LEVEL` - **Optional** - Logging level (defaults to "INFO")
- `MIN_TASK_WORDS` - **Optional** - Minimum task summary words (default: 3)
- `MAX_TASK_WORDS` - **Optional** - Maximum task summary words (default: 12)

### Using setup-env.ps1 Script
The `setup-env.ps1` PowerShell script provides:
- ✅ Automatic loading of all variables from `.env`
- ✅ Validation of required keys
- ✅ Masked display of API keys for security
- ✅ Clear error messages if keys are missing

Run it before starting the bot:
```powershell
.\setup-env.ps1
```

### Timezone Configuration
The bot is configured for Malaysia timezone (`Asia/Kuala_Lumpur` - UTC+8).
To change the timezone, edit `src/config/settings.py`:
```python
timezone: pytz.tzinfo.BaseTzInfo = field(default_factory=lambda: pytz.timezone('Your/Timezone'))
```

## First Run

### Quick Start (Using start-bot.bat)
```bash
# The start script does everything automatically:
# 1. Loads environment from .env
# 2. Activates virtual environment
# 3. Starts the bot
.\start-bot.bat
```

### Manual Start
```bash
# 1. Load environment variables
.\setup-env.ps1

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Start the bot
python src\bot.py
```

### Connect to Telegram
1. Open Telegram
2. Search for your bot by username
3. Send `/start` command

### Connect to Outlook
1. Send `/connectoutlook` command
2. Follow the device code authentication flow
3. Sign in with your Microsoft account

### Test Task Creation
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

### API Keys Protection
- ✅ `.env` file is excluded from git (via `.gitignore`)
- ✅ Never commit `.env` to version control
- ✅ Use `.env.template` as reference for required keys
- ✅ `setup-env.ps1` displays masked values only
- ⚠️ Keep `.env` file permissions restricted
- ⚠️ Regenerate keys if accidentally exposed

### Environment Variables
- Use `.env` file for local development
- Use system environment variables for production/servers
- Never hardcode API keys in source code

### Bot Token Security
- Treat as password - keep secret
- Regenerate via @BotFather if compromised
- Don't share in screenshots or logs

### Microsoft Authentication
- Tokens stored in memory only (via TokenManager class)
- Re-authentication required per session
- No persistent token storage
- Device code flow provides secure authentication