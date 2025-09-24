@echo off
REM Start Bot Script - Runs the bot from the new organized structure

set "PATH=%PATH%;C:\Program Files\Git\bin"

echo ==================================================
echo   Starting Telegram Task Bot
echo ==================================================

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  Virtual environment not found - using system Python
)

REM Set environment variables if not already set
if "%GEMINI_API_KEY%"=="" (
    echo ⚠️  GEMINI_API_KEY not set - bot may not work properly
)

REM Start the bot
echo Starting bot from src\bot.py...
python src\bot.py

pause