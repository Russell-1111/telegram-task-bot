# Telegram Task Bot Configuration Template
# Copy this file to config.py and fill in your actual values

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token_here"

# Google Gemini AI Configuration
GEMINI_API_KEY = "your_gemini_api_key_here"

# Microsoft Azure Configuration
CLIENT_ID = "your_azure_client_id_here"
AUTHORITY = "https://login.microsoftonline.com/your_tenant_id_here"

# Bot Settings
MALAYSIA_TIMEZONE = "Asia/Kuala_Lumpur"
MIN_TASK_WORDS = 3
MAX_TASK_WORDS = 12
DEFAULT_TASK_TIME = "17:00:00"  # 5:00 PM

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# State Persistence Configuration (Optional)
# Uncomment and set these to enable persistent state across bot restarts
# STATE_ENCRYPTION_KEY = "your_32_byte_base64_encoded_fernet_key_here"  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# DATA_DIR = "data"  # Directory for state files (default: "data")
# ENABLE_PERSISTENCE = True  # Set to False to disable persistence (default: True)
# BACKUP_RETENTION_COUNT = 3  # Number of backup files to keep (default: 3)
# AUTO_SAVE_INTERVAL_SECONDS = 300  # Auto-save interval in seconds (default: 300 = 5 minutes)