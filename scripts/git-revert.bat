@echo off
REM Revert to stable version script

set "PATH=%PATH%;C:\Program Files\Git\bin"

echo ⚠️  WARNING: This will discard ALL current changes!
echo This will revert to the stable version (v1.0)
echo.
set /p confirm="Are you sure? (y/N): "

if /i "%confirm%"=="y" (
    echo Reverting to stable version...
    git checkout stable-v1.0
    git checkout -b recovery-%date:~-4%-%date:~4,2%-%date:~7,2%
    echo.
    echo ✅ Reverted to stable version!
    echo You are now on a new recovery branch.
    echo Your stable bot should be working again.
) else (
    echo Operation cancelled.
)