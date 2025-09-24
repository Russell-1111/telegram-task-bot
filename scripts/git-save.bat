@echo off
REM Quick save script - commits current changes

set "PATH=%PATH%;C:\Program Files\Git\bin"

if "%1"=="" (
    set "MESSAGE=Quick save: %date% %time%"
) else (
    set "MESSAGE=%*"
)

echo Saving changes with message: %MESSAGE%
git add .
git commit -m "%MESSAGE%"

echo.
echo ✅ Changes saved successfully!
echo Current status:
git status --short