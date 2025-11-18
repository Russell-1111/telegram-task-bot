import logging
import sys
import signal
import atexit
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config.settings import config
from utils.lock_manager import BotLockManager
from utils import EncryptionManager, TokenManager, UserStateManager, AutoSaveThread
from handlers import start, connect_outlook, my_tasks, echo
from handlers.command_handlers import set_token_manager
from handlers.message_handlers import set_managers

logger = logging.getLogger(__name__)

# Global references for graceful shutdown
token_manager = None
state_manager = None
auto_save_thread = None


def error_handler(update: Update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def graceful_shutdown(signum, frame):
    """Handle shutdown signals and save state before exiting."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    global token_manager, state_manager, auto_save_thread
    
    # Stop auto-save thread first
    if auto_save_thread and auto_save_thread.is_alive():
        logger.info("Stopping auto-save thread...")
        auto_save_thread.stop(timeout=5.0)
    
    # Save state with timeout
    import time
    start_time = time.time()
    timeout = 5.0  # 5 second timeout
    
    try:
        if token_manager:
            if token_manager.save_state():
                logger.info("Token state saved successfully")
            else:
                logger.warning("Failed to save token state")
        
        if state_manager:
            if state_manager.save_state():
                logger.info("User state saved successfully")
            else:
                logger.warning("Failed to save user state")
        
        elapsed = time.time() - start_time
        if elapsed > timeout:
            logger.warning(f"Shutdown save exceeded timeout ({elapsed:.2f}s > {timeout}s)")
        else:
            logger.info(f"State saved in {elapsed:.2f}s")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
    
    logger.info("Graceful shutdown complete")
    sys.exit(0)


def save_state_on_exit():
    """atexit handler to save state on normal program termination."""
    logger.info("Normal exit detected, saving state...")
    global token_manager, state_manager, auto_save_thread
    
    # Stop auto-save thread
    if auto_save_thread and auto_save_thread.is_alive():
        auto_save_thread.stop(timeout=5.0)
    
    try:
        if token_manager:
            token_manager.save_state()
        if state_manager:
            state_manager.save_state()
    except Exception as e:
        logger.error(f"Error saving state on exit: {e}")


def main():
    global token_manager, state_manager, auto_save_thread
    
    # Initialize persistence if enabled
    if config.enable_persistence:
        try:
            logger.info("Initializing persistence...")
            
            # Initialize encryption manager
            if config.state_encryption_key:
                encryption_manager = EncryptionManager(config.state_encryption_key)
                logger.info("Using encryption key from configuration")
            else:
                encryption_manager = EncryptionManager.create_with_new_key()
                key = encryption_manager.get_key()
                logger.warning("=" * 60)
                logger.warning("AUTO-GENERATED ENCRYPTION KEY")
                logger.warning(f"Key: {key}")
                logger.warning("IMPORTANT: Set STATE_ENCRYPTION_KEY environment variable")
                logger.warning("to preserve this key across restarts!")
                logger.warning("=" * 60)
            
            # Initialize managers with persistence
            token_manager = TokenManager(
                encryption_manager=encryption_manager,
                token_file_path=f"{config.data_dir}/tokens.enc",
                persistence_enabled=True
            )
            state_manager = UserStateManager(
                state_file_path=f"{config.data_dir}/user_state.json",
                persistence_enabled=True
            )
            
            # Load existing state
            tokens_loaded = token_manager.load_state()
            state_loaded = state_manager.load_state()
            
            logger.info(f"Persistence enabled - tokens: {'restored' if tokens_loaded else 'empty'}, "
                       f"state: {'restored' if state_loaded else 'empty'}")
            
            # Start auto-save thread
            if config.auto_save_interval_seconds > 0:
                auto_save_thread = AutoSaveThread(
                    token_manager,
                    state_manager,
                    interval_seconds=config.auto_save_interval_seconds
                )
                auto_save_thread.start()
                logger.info(f"Auto-save thread started with {config.auto_save_interval_seconds}s interval")
            else:
                logger.info("Auto-save disabled (interval set to 0)")
        except Exception as e:
            logger.error(f"Failed to initialize persistence: {e}")
            logger.warning("Falling back to in-memory storage")
            token_manager = TokenManager()
            state_manager = UserStateManager()
    else:
        logger.info("Persistence disabled - using in-memory storage")
        token_manager = TokenManager()
        state_manager = UserStateManager()
    
    # Set managers in handlers
    set_token_manager(token_manager)
    set_managers(token_manager, state_manager)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)
    
    # Register atexit handler for normal termination
    atexit.register(save_state_on_exit)
    
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
