# ============================================================
# Telegram Task Bot - Environment Setup Script
# ============================================================
# This script loads environment variables from .env file
# and sets them for the current PowerShell session
#
# Usage:
#   1. Copy .env.template to .env
#   2. Fill in your API keys in .env
#   3. Run: .\setup-env.ps1
#   4. Run your bot: python src\bot.py
# ============================================================

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Telegram Task Bot - Environment Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please follow these steps:" -ForegroundColor Yellow
    Write-Host "  1. Copy .env.template to .env" -ForegroundColor Yellow
    Write-Host "     Copy-Item .env.template .env" -ForegroundColor Gray
    Write-Host "  2. Edit .env and add your API keys" -ForegroundColor Yellow
    Write-Host "  3. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "Loading environment variables from .env..." -ForegroundColor Green

# Read .env file and set environment variables
$envVars = @{}
$requiredVars = @("TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY", "MS_CLIENT_ID")
$optionalVars = @("MS_TENANT_ID")
$loadedVars = @()
$missingVars = @()

# Parse .env file
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    
    # Skip empty lines and comments
    if ($line -eq "" -or $line.StartsWith("#")) {
        return
    }
    
    # Parse KEY=VALUE
    if ($line -match "^([^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        
        # Remove surrounding quotes if present
        if ($value -match '^"(.*)"$') {
            $value = $matches[1]
        } elseif ($value -match "^'(.*)'$") {
            $value = $matches[1]
        }
        
        # Skip placeholder values
        if ($value -match "your_.*_here" -or $value -eq "") {
            if ($requiredVars -contains $key) {
                $missingVars += $key
            }
            return
        }
        
        # Set environment variable
        Set-Item -Path "env:$key" -Value $value
        $envVars[$key] = $value
        $loadedVars += $key
        
        # Show masked value
        $maskedValue = if ($value.Length -gt 8) {
            $value.Substring(0, 4) + "..." + $value.Substring($value.Length - 4)
        } else {
            "***"
        }
        Write-Host "  [OK] $key = $maskedValue" -ForegroundColor Gray
    }
}

Write-Host ""

# Check for missing required variables
if ($missingVars.Count -gt 0) {
    Write-Host "WARNING: Missing required environment variables!" -ForegroundColor Yellow
    Write-Host ""
    foreach ($var in $missingVars) {
        Write-Host "  [MISSING] $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please edit .env and add the missing values." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Success summary
Write-Host "Environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Loaded variables:" -ForegroundColor Cyan
foreach ($var in $loadedVars) {
    $icon = if ($requiredVars -contains $var) { "[REQUIRED]" } else { "[OPTIONAL]" }
    Write-Host "  $icon $var" -ForegroundColor Gray
}
Write-Host ""

# Show next steps
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Activate virtual environment:" -ForegroundColor White
Write-Host "     .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. Run the bot:" -ForegroundColor White
Write-Host "     python src\bot.py" -ForegroundColor Gray
Write-Host "  3. Or use the start script:" -ForegroundColor White
Write-Host "     .\start-bot.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
