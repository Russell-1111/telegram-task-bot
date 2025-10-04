@echo off
setlocal enabledelayedexpansion
REM Start Bot Script - Runs the bot from the new organized structure

set "PATH=%PATH%;C:\Program Files\Git\bin"

echo ==================================================
echo   Starting Telegram Task Bot
echo ==================================================
echo.

REM Load environment variables from .env file
echo Loading environment variables from .env...
echo.

if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create .env file with your API keys.
    echo You can copy .env.template to .env and edit it.
    echo.
    pause
    exit /b 1
)

REM Parse .env file and set environment variables
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    set "line=%%a"
    set "value=%%b"
    
    REM Skip empty lines and comments
    if not "!line!"=="" (
        if not "!line:~0,1!"=="#" (
            REM Remove quotes from value
            set "cleanValue=!value:"=!"
            
            REM Set the environment variable
            set "%%a=!cleanValue!"
            echo   [OK] %%a loaded
        )
    )
)

echo.
echo Environment variables loaded successfully!
echo.

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found - using system Python
)

echo.

REM Start the bot
echo Starting bot from src\bot.py...
python src\bot.py

pause