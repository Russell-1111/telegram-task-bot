@echo off
REM Git Helper Script for Telegram Bot Project
REM This script adds Git to PATH and provides common Git commands

set "PATH=%PATH%;C:\Program Files\Git\bin"

echo ==================================================
echo   Telegram Bot Project - Git Helper
echo ==================================================
echo Current Git Status:
git status --short
echo.
echo Available Commands:
echo   git-save.bat "message"  - Save current changes
echo   git-revert.bat          - Revert to stable version
echo   git-history.bat         - View commit history
echo   git-branches.bat        - View all branches
echo.
echo Current branch:
git branch --show-current
echo.
echo Last commit:
git log -1 --oneline
echo ==================================================