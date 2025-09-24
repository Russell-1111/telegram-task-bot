@echo off
REM View commit history

set "PATH=%PATH%;C:\Program Files\Git\bin"

echo ==================================================
echo   Commit History
echo ==================================================
git log --oneline --graph --decorate --all -10
echo.
echo For full history, use: git log
echo ==================================================