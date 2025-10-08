# GitHub Upload Guide - Telegram Task Bot

**Last Updated:** October 8, 2025

---

## ⚠️ CRITICAL: Security Pre-Flight Checklist

**BEFORE** pushing to GitHub, complete these steps to prevent exposing secrets:

### 🔒 Step 1: Remove Sensitive Files from Staging

```powershell
# UNSTAGE the .env file (CRITICAL!)
git restore --staged .env

# Verify .env is NOT staged
git status

# Expected: .env should appear under "Untracked files" or "Changes not staged"
```

### 🔍 Step 2: Verify No Secrets in Staged Files

```powershell
# Scan staged files for API keys/tokens
Select-String -Path "src\**\*.py" -Pattern "(AIza|sk-|xox|ghp_|Bot.*:)" -CaseSensitive

# Check if config.py exists (should NOT exist - use config_template.py)
Get-ChildItem -Path "src\config\" -Filter "config.py" -Recurse

# Expected: NO matches for secrets, NO config.py file
```

### 🧹 Step 3: Clean Up Unwanted Files

```powershell
# Remove Python cache files (already in .gitignore but staged)
git restore --staged **/__pycache__/
git restore --staged bot.lock

# Remove test files (if you want - optional)
git restore --staged test_*.py

# Verify cleanup
git status
```

---

## 📋 Step-by-Step GitHub Upload Process

### Phase 1: Repository Creation (GitHub Website)

1. **Go to GitHub**: https://github.com/new
2. **Repository Settings**:
   - **Name**: `telegram-task-bot` (or your preferred name)
   - **Description**: "AI-powered Telegram bot for Outlook task management with Google Gemini integration"
   - **Visibility**: ⚠️ **PRIVATE** recommended (contains architecture of personal bot)
   - **Initialize**: 
     - ❌ Do NOT add README (you already have one)
     - ❌ Do NOT add .gitignore (you already have one)
     - ✅ Add license (choose MIT or your preference)

3. **Click "Create repository"**

### Phase 2: Prepare Local Repository

```powershell
# Navigate to project directory
cd C:\Users\User\Downloads\telegram_task_bot

# Verify current branch
git branch

# Create main branch if needed (you're on refactor/phase1-quick-wins)
git checkout -b main

# Review what will be committed
git status

# Review staged changes
git diff --staged

# If everything looks good, commit
git commit -m "Initial commit: Telegram Task Bot with Outlook integration

Features:
- Google Gemini AI for task intent detection
- Microsoft Outlook Tasks integration
- Multi-layer validation (input relevance, summary, dates)
- Malaysia timezone support (UTC+8)
- Comprehensive documentation (SETUP, API, EXAMPLES, TESTING)
- Service layer architecture (LLM, Outlook, State, Token managers)
- Phase 1-3 refactoring completed (modular design)

Architecture:
- Python 3.13.7
- python-telegram-bot
- google-generativeai (Gemini 2.5 Flash)
- MSAL (Microsoft Authentication Library)
- pytz (timezone handling)
"
```

### Phase 3: Connect and Push to GitHub

```powershell
# Add GitHub remote (replace YOUR-USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/telegram-task-bot.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main
```

### Phase 4: Verify Upload Success

1. **Visit your repository**: https://github.com/YOUR-USERNAME/telegram-task-bot
2. **Check**:
   - ✅ README.md displays correctly
   - ✅ All documentation files visible (docs/ folder)
   - ✅ Source code visible (src/ folder)
   - ❌ `.env` file is NOT visible (should be hidden by .gitignore)
   - ❌ No API keys in any visible files
   - ❌ `__pycache__/` folders NOT visible

---

## 🛡️ Security Verification Commands

### Before Pushing

```powershell
# 1. Check .gitignore is working
git check-ignore .env
# Expected output: .env (means it's ignored)

# 2. List what will be pushed
git ls-files | Select-String ".env"
# Expected: NO output (means .env is not tracked)

# 3. Check for hardcoded secrets
Select-String -Path "src\**\*.py" -Pattern "(AIza|sk-|xox|ghp_|Bot.*[0-9]{10}:)" -CaseSensitive
# Expected: NO matches

# 4. Verify template files exist
Get-ChildItem -Path . -Filter "*.template" -Recurse
# Expected: .env.template, config_template.py
```

### After Pushing

```powershell
# Clone your repo to a temporary location to verify
cd C:\Users\User\Downloads
git clone https://github.com/YOUR-USERNAME/telegram-task-bot.git telegram-task-bot-verify
cd telegram-task-bot-verify

# Check if .env exists (it SHOULD NOT)
Get-ChildItem -Path . -Filter ".env" -Recurse
# Expected: NO .env file

# Check if secrets are exposed
Select-String -Path "**\*.py" -Pattern "(AIza|sk-|xox|ghp_)" -CaseSensitive
# Expected: NO matches

# Clean up verification clone
cd ..
Remove-Item -Recurse -Force telegram-task-bot-verify
```

---

## 📚 Documentation Files to Include

### Essential Documentation (Already Present)

- ✅ **README.md** - Project overview
- ✅ **SETUP.md** - Environment setup guide
- ✅ **TESTING-GUIDE.md** - How to test the bot
- ✅ **ENVIRONMENT-SETUP.md** - Detailed environment configuration
- ✅ **API.md** - Developer API reference
- ✅ **EXAMPLES.md** - Code examples
- ✅ **GIT-COMMIT-GUIDE.md** - Commit message standards
- ✅ **FEATURE-PLAN.md** - Future feature roadmap

### Historical Documentation (Archive)

- ✅ **PHASE1-SUMMARY.md** - Configuration/validators extraction
- ✅ **PHASE2-SUMMARY.md** - Service layer creation
- ✅ **PHASE3-SUMMARY.md** - State management refactoring
- ✅ **ARCHITECTURE-REVIEW.md** - Initial architecture analysis

### Template Files (MUST INCLUDE)

- ✅ **.env.template** - Environment variables template
- ✅ **config/config_template.py** - Configuration file template

---

## 🎯 Repository Configuration (Post-Upload)

### Add Repository Topics (GitHub Website)

1. Go to repository settings
2. Click "Manage topics"
3. Add relevant tags:
   - `telegram-bot`
   - `python`
   - `outlook-api`
   - `google-gemini`
   - `task-management`
   - `microsoft-graph`
   - `ai-integration`
   - `natural-language-processing`

### Create GitHub Wiki (Optional)

1. Go to repository → Wiki tab
2. Create pages for:
   - **Home**: Project overview
   - **Installation**: Detailed setup guide
   - **Architecture**: System design diagrams
   - **API Reference**: Link to API.md
   - **Troubleshooting**: Common issues

### Enable GitHub Pages for Documentation (Optional)

1. Settings → Pages
2. Source: `main` branch → `/docs` folder
3. Theme: Choose a theme
4. Access at: https://YOUR-USERNAME.github.io/telegram-task-bot

---

## 🚨 Emergency: If You Accidentally Pushed Secrets

If you accidentally pushed `.env` or secrets to GitHub:

### Immediate Actions

```powershell
# 1. IMMEDIATELY revoke all API keys/tokens
# - Telegram: Contact @BotFather to regenerate token
# - Gemini: Delete API key at https://aistudio.google.com/app/apikey
# - Azure: Rotate client secrets in Azure Portal

# 2. Remove file from Git history (requires force push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push to GitHub (DANGER: rewrites history)
git push origin --force --all

# 4. Contact GitHub Support
# - Report exposed secrets
# - They may automatically disable tokens they detect
```

### Prevention

- ✅ Use `.gitignore` (already configured)
- ✅ Use `git-secrets` tool to prevent commits with secrets
- ✅ Enable GitHub secret scanning (automatic for public repos)
- ✅ Use environment variables, never hardcode secrets

---

## 📊 What Gets Uploaded vs What Stays Local

### ✅ Uploaded to GitHub (Public/Private Repo)

```
├── README.md
├── requirements.txt
├── setup-env.ps1
├── start-bot.bat
├── .gitignore
├── .env.template ✅ (template only)
├── config/
│   └── config_template.py ✅ (template only)
├── src/ (all Python source code)
├── docs/ (all documentation)
├── scripts/ (git helper scripts)
└── test_*.py (optional - your choice)
```

### ❌ Stays Local (Ignored by Git)

```
├── .env ❌ (YOUR secrets)
├── .venv/ ❌ (virtual environment)
├── __pycache__/ ❌ (Python cache)
├── bot.lock ❌ (runtime lock file)
├── *.log ❌ (log files)
├── .msal_token_cache.json ❌ (OAuth tokens)
└── config/config.py ❌ (if it exists)
```

---

## 🎨 Optional: Enhance Repository Presentation

### Add Badges to README.md

```markdown
![Python Version](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Telegram Bot](https://img.shields.io/badge/telegram-bot-blue?logo=telegram)
```

### Add Screenshots

1. Create `docs/screenshots/` folder
2. Add images of bot in action
3. Reference in README.md:
   ```markdown
   ![Bot Demo](docs/screenshots/bot-demo.png)
   ```

### Add Architecture Diagram

1. Create diagram (draw.io, Mermaid, etc.)
2. Save as `docs/architecture-diagram.png`
3. Reference in README.md

---

## ✅ Final Checklist Before Pushing

- [ ] `.env` is **NOT** staged (run `git status`)
- [ ] No hardcoded secrets in source code
- [ ] `.env.template` exists and has placeholder values
- [ ] `.gitignore` is properly configured
- [ ] README.md is clear and comprehensive
- [ ] All documentation is up-to-date
- [ ] Virtual environment (`.venv/`) is ignored
- [ ] `__pycache__/` folders are ignored
- [ ] Commit message is descriptive
- [ ] Repository visibility is set (public/private)
- [ ] You've decided on a license (MIT recommended)

---

## 📞 Helpful Resources

- **GitHub Documentation**: https://docs.github.com/en/get-started
- **Git Best Practices**: https://git-scm.com/book/en/v2
- **Python .gitignore Template**: https://github.com/github/gitignore/blob/main/Python.gitignore
- **GitHub Security Best Practices**: https://docs.github.com/en/code-security
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Microsoft Graph API**: https://learn.microsoft.com/en-us/graph/

---

## 🎉 Success Indicators

After successful upload, you should see:

1. ✅ Repository visible at `https://github.com/YOUR-USERNAME/telegram-task-bot`
2. ✅ All documentation rendered correctly
3. ✅ Source code organized in folders
4. ✅ No sensitive information visible
5. ✅ `.env.template` provides clear setup instructions
6. ✅ README displays with formatting
7. ✅ License file visible

---

**Ready to upload?** Follow the steps sequentially and verify each checkpoint!

**Questions?** Review the documentation or check GitHub's help pages.

**Happy documenting!** 🚀
