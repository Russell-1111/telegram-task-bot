"""
Centralized configuration for Telegram Task Bot

This module provides all application settings loaded from environment variables
with proper validation and defaults. No hardcoded secrets allowed!
"""
import os
import sys
import logging
import pytz
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Main application configuration with validation"""
    
    # ===== API Keys & Tokens =====
    gemini_api_key: str
    telegram_bot_token: str
    
    # ===== Microsoft Graph API Configuration =====
    ms_client_id: str = "your_client_id_here"
    ms_tenant_id: str = "common"
    ms_scopes: List[str] = field(default_factory=lambda: [
        "Tasks.ReadWrite",
        "offline_access"
    ])
    
    # ===== Application Settings =====
    timezone: pytz.tzinfo.BaseTzInfo = field(default_factory=lambda: pytz.timezone('Asia/Kuala_Lumpur'))
    gemini_model_name: str = "gemini-2.5-flash"
    
    # ===== Task Validation Settings =====
    min_task_words: int = 3
    max_task_words: int = 12
    max_tasks_display: int = 10
    
    # ===== Rate Limiting =====
    rate_limit_seconds: int = 60  # Rate limit for /mytasks command
    
    # ===== File Paths =====
    lock_file_path: str = "bot.lock"
    
    # ===== State Persistence Configuration =====
    state_encryption_key: str = None  # Will be auto-generated if not provided
    data_dir: str = "data"
    enable_persistence: bool = True
    backup_retention_count: int = 3
    auto_save_interval_seconds: int = 300  # 5 minutes
    
    # ===== Logging Configuration =====
    log_level: str = "INFO"
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        # Validate required fields
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Please set it before starting the bot."
            )
        
        if not self.telegram_bot_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN environment variable is required. "
                "Please set it before starting the bot."
            )
        
        # Validate word count settings
        if self.min_task_words > self.max_task_words:
            raise ValueError(
                f"min_task_words ({self.min_task_words}) cannot be greater than "
                f"max_task_words ({self.max_task_words})"
            )
        
        # Validate persistence settings
        if self.enable_persistence:
            # Validate backup retention count
            if self.backup_retention_count < 1:
                logger.warning(
                    f"backup_retention_count ({self.backup_retention_count}) is less than 1. "
                    f"Using default value 3."
                )
                self.backup_retention_count = 3
            elif self.backup_retention_count > 10:
                logger.warning(
                    f"backup_retention_count ({self.backup_retention_count}) exceeds 10. "
                    f"Using maximum value 10."
                )
                self.backup_retention_count = 10
            
            # Validate encryption key format if provided
            if self.state_encryption_key:
                try:
                    import base64
                    key_bytes = base64.urlsafe_b64decode(self.state_encryption_key)
                    if len(key_bytes) != 32:
                        raise ValueError(
                            f"STATE_ENCRYPTION_KEY must be a 32-byte base64-encoded Fernet key. "
                            f"Got {len(key_bytes)} bytes after decoding."
                        )
                except Exception as e:
                    raise ValueError(
                        f"Invalid STATE_ENCRYPTION_KEY format: {e}. "
                        f"Generate a valid key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                    )
            
            # Validate/create data directory
            import pathlib
            data_path = pathlib.Path(self.data_dir)
            try:
                data_path.mkdir(parents=True, exist_ok=True)
                # Test write permissions
                test_file = data_path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as e:
                raise ValueError(
                    f"Cannot write to data directory '{self.data_dir}': {e}. "
                    f"Please check permissions or set DATA_DIR to a writable location."
                )
        
        logger.info("Configuration loaded successfully")
        logger.info(f"Timezone: {self.timezone}")
        logger.info(f"Task word limits: {self.min_task_words}-{self.max_task_words}")
        if self.enable_persistence:
            logger.info(f"Persistence enabled: data_dir={self.data_dir}, backups={self.backup_retention_count}")
        else:
            logger.warning("Persistence is DISABLED - state will not be saved across restarts")
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Load configuration from environment variables
        
        Returns:
            AppConfig: Validated configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Load required environment variables
        gemini_key = os.getenv("GEMINI_API_KEY")
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Load optional environment variables with defaults
        ms_client_id = os.getenv("MS_CLIENT_ID", "your_client_id_here")
        ms_tenant_id = os.getenv("MS_TENANT_ID", "common")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Parse integer settings
        min_words = int(os.getenv("MIN_TASK_WORDS", "3"))
        max_words = int(os.getenv("MAX_TASK_WORDS", "12"))
        max_display = int(os.getenv("MAX_TASKS_DISPLAY", "10"))
        rate_limit = int(os.getenv("RATE_LIMIT_SECONDS", "60"))
        
        # Parse persistence settings
        encryption_key = os.getenv("STATE_ENCRYPTION_KEY")
        data_dir = os.getenv("DATA_DIR", "data")
        enable_persistence = os.getenv("ENABLE_PERSISTENCE", "true").lower() in ("true", "1", "yes", "on")
        backup_retention = int(os.getenv("BACKUP_RETENTION_COUNT", "3"))
        auto_save_interval = int(os.getenv("AUTO_SAVE_INTERVAL_SECONDS", "300"))
        
        return cls(
            gemini_api_key=gemini_key,
            telegram_bot_token=telegram_token,
            ms_client_id=ms_client_id,
            ms_tenant_id=ms_tenant_id,
            log_level=log_level,
            min_task_words=min_words,
            max_task_words=max_words,
            max_tasks_display=max_display,
            rate_limit_seconds=rate_limit,
            state_encryption_key=encryption_key,
            data_dir=data_dir,
            enable_persistence=enable_persistence,
            backup_retention_count=backup_retention,
            auto_save_interval_seconds=auto_save_interval
        )
    
    def setup_logging(self):
        """Configure logging based on settings"""
        logging.basicConfig(
            format=self.log_format,
            level=getattr(logging, self.log_level.upper())
        )


# ===== Global Configuration Instance =====
# This is the single source of truth for all configuration
try:
    config = AppConfig.from_env()
    config.setup_logging()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)


# ===== Constants =====
# Non-configurable application constants

class Constants:
    """Application constants that don't change"""
    
    # Date format strings
    DATE_FORMAT_ISO = "%Y-%m-%d"
    DATETIME_FORMAT_OUTLOOK = "%Y-%m-%dT%H:%M:%S.0000000"
    
    # Default task settings
    DEFAULT_TASK_TIME_HOUR = 17  # 5:00 PM
    DEFAULT_TASK_TIME_MINUTE = 0
    
    # LLM Intent types
    INTENT_CREATE_TASK = "create_task"
    INTENT_UPDATE_DUE_DATE = "update_due_date"
    INTENT_UNKNOWN = "unknown"
    
    # Telegram formatting
    TELEGRAM_MAX_MESSAGE_LENGTH = 4096
    
    # Stop words for task summary generation
    STOP_WORDS = {
        'i', 'me', 'to', 'a', 'an', 'the', 'and', 'or', 
        'but', 'in', 'on', 'at', 'by', 'for', 'with', 'from'
    }


constants = Constants()
