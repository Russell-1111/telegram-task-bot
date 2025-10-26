@echo off
REM ============================================
REM Automated Redundant Code Cleanup Script
REM Branch: cleanup/remove-redundant-code
REM ============================================

echo.
echo ========================================
echo  REDUNDANT CODE CLEANUP SCRIPT
echo ========================================
echo.

REM Check if on correct branch
git branch --show-current > temp_branch.txt
set /p CURRENT_BRANCH=<temp_branch.txt
del temp_branch.txt

if not "%CURRENT_BRANCH%"=="cleanup/remove-redundant-code" (
    echo ERROR: Not on cleanup/remove-redundant-code branch!
    echo Current branch: %CURRENT_BRANCH%
    echo.
    echo Please run: git checkout cleanup/remove-redundant-code
    echo.
    pause
    exit /b 1
)

echo Current branch: %CURRENT_BRANCH%
echo.
echo This script will remove redundant files in 2 phases:
echo   Phase 1: Test file and cache directories (ZERO RISK)
echo   Phase 2: Redundant documentation files (LOW RISK)
echo.
echo Main branch will NOT be affected.
echo You can rollback anytime with: git checkout main
echo.

pause

REM ============================================
REM PHASE 1: SAFE DELETIONS (Zero Risk)
REM ============================================

echo.
echo ========================================
echo  PHASE 1: SAFE DELETIONS
echo ========================================
echo.

REM Delete redundant test file
if exist test_llm_condensing.py (
    echo [1/3] Deleting test_llm_condensing.py...
    del /f test_llm_condensing.py
    echo       Done!
) else (
    echo [1/3] test_llm_condensing.py already removed
)

REM Delete cache directories
echo [2/3] Removing __pycache__ directories...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo       Removing %%d
        rd /s /q "%%d"
    )
)
echo       Done!

REM Delete coverage file
if exist .coverage (
    echo [3/3] Deleting .coverage file...
    del /f .coverage
    echo       Done!
) else (
    echo [3/3] .coverage already removed
)

echo.
echo Phase 1 complete!
echo.

REM Commit Phase 1
echo Committing Phase 1 changes...
git add -A
git commit -m "chore: remove redundant test file and cache directories"
echo.

REM ============================================
REM PHASE 2: DOCUMENTATION CLEANUP (Low Risk)
REM ============================================

echo.
echo ========================================
echo  PHASE 2: DOCUMENTATION CLEANUP
echo ========================================
echo.
echo This will remove 3 overlapping documentation files:
echo   - docs/FIX-SUMMARY.md
echo   - docs/LLM-CONDENSING-FIX.md
echo   - docs/CRITICAL-BUG-FIX.md
echo.
echo Content is preserved in docs/SESSION-FIXES-2025-10-06.md
echo.

choice /C YN /M "Continue with Phase 2"
if errorlevel 2 goto skip_phase2

REM Delete redundant documentation
if exist docs\FIX-SUMMARY.md (
    echo [1/3] Deleting docs/FIX-SUMMARY.md...
    del /f docs\FIX-SUMMARY.md
    echo       Done!
) else (
    echo [1/3] docs/FIX-SUMMARY.md already removed
)

if exist docs\LLM-CONDENSING-FIX.md (
    echo [2/3] Deleting docs/LLM-CONDENSING-FIX.md...
    del /f docs\LLM-CONDENSING-FIX.md
    echo       Done!
) else (
    echo [2/3] docs/LLM-CONDENSING-FIX.md already removed
)

if exist docs\CRITICAL-BUG-FIX.md (
    echo [3/3] Deleting docs/CRITICAL-BUG-FIX.md...
    del /f docs\CRITICAL-BUG-FIX.md
    echo       Done!
) else (
    echo [3/3] docs/CRITICAL-BUG-FIX.md already removed
)

echo.
echo Phase 2 complete!
echo.

REM Commit Phase 2
echo Committing Phase 2 changes...
git add -A
git commit -m "docs: consolidate redundant documentation files"
echo.

goto phase3

:skip_phase2
echo.
echo Phase 2 skipped.
echo.

REM ============================================
REM PHASE 3: VERIFICATION
REM ============================================

:phase3
echo.
echo ========================================
echo  PHASE 3: VERIFICATION
echo ========================================
echo.
echo Running tests to verify nothing broke...
echo.

python -m pytest tests/ -v

if errorlevel 1 (
    echo.
    echo ERROR: Tests failed!
    echo Something may have broken. Review the output above.
    echo.
    echo To rollback: git checkout main
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  CLEANUP COMPLETE!
echo ========================================
echo.
echo Summary:
echo   - Removed redundant test file
echo   - Cleaned up cache directories
echo   - Consolidated documentation files
echo   - All tests passing
echo.
echo The cleanup branch is ready to merge to main!
echo.
echo Next steps:
echo   1. Review changes: git log --oneline
echo   2. Push branch: git push origin cleanup/remove-redundant-code
echo   3. Merge to main: git checkout main ^&^& git merge cleanup/remove-redundant-code
echo.
echo Or rollback: git checkout main ^&^& git branch -D cleanup/remove-redundant-code
echo.

pause
