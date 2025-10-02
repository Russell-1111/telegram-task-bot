import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import config
from utils.lock_manager import BotLockManager
from handlers import start, connect_outlook, my_tasks, echo

logger = logging.getLogger(__name__)


def error_handler(update: Update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def main():
    try:
        application = Application.builder().token(config.telegram_bot_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("connectoutlook", connect_outlook))
        application.add_handler(CommandHandler("mytasks", my_tasks))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        application.add_error_handler(error_handler)
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot started and is polling for updates...")
    except Exception as e:
        if "409" in str(e) or "Conflict" in str(e):
            logger.error("Bot conflict detected!")
        else:
            logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == '__main__':
    lock_manager = BotLockManager(config.lock_file_path)
    if not lock_manager.acquire_lock():
        logger.error("Another bot instance is running. Exiting.")
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        lock_manager.release_lock()
