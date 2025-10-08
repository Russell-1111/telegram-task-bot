# GitHub Upload Guide

## 📚 How to Upload This Project to GitHub

This guide walks you through uploading your Telegram Task Bot project to GitHub for documentation and portfolio purposes.

---

## 🎯 Prerequisites

### 1. Install Git (if not already installed)
- **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
- **Verify installation**: Open PowerShell and run:
  ```powershell
  git --version
  ```

### 2. Create a GitHub Account
- Go to [github.com](https://github.com)
- Sign up for a free account if you don't have one

---

## 🔐 CRITICAL: Protect Your Secrets

**⚠️ NEVER commit sensitive information to GitHub!**

Before uploading, ensure these files contain NO real credentials:

### Files to Check:
1. `config/config_template.py` - Should only have placeholder values
2. `.env` files - Should NOT be committed (add to `.gitignore`)
3. Any files with API keys, tokens, or passwords

### Action Required:

#### Step 1: Create `.gitignore` File
The project should already have a `.gitignore` file. If not, create one:

```gitignore
# Environment variables (NEVER COMMIT THESE!)
.env
*.env
config/config.py

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Virtual environment
.venv/
venv/
ENV/

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Lock files (process locks)
*.lock
bot.lock

# Logs
*.log

# Test files (optional - you may want to commit these)
test_*.py

# Sensitive data
tokens/
credentials/
*.token
```

#### Step 2: Verify No Secrets in Code
Check these files for hardcoded secrets:
```powershell
# Search for potential secrets
Select-String -Path "src\**\*.py" -Pattern "(api_key|token|password|secret)" -CaseSensitive
```

If you find any hardcoded secrets, replace them with environment variable references:
```python
# ❌ BAD:
api_key = "AIzaSyC_actual_key_here"

# ✅ GOOD:
api_key = os.getenv("GEMINI_API_KEY")
```

---

## 📤 Upload Process

### Method 1: GitHub Desktop (Easiest)

#### Step 1: Download GitHub Desktop
- Download from [desktop.github.com](https://desktop.github.com)
- Install and sign in with your GitHub account

#### Step 2: Create Repository
1. Open GitHub Desktop
2. Click **File** → **New Repository**
3. Fill in details:
   - **Name**: `telegram-task-bot` (or your preferred name)
   - **Description**: "AI-powered Telegram bot for Outlook task management"
   - **Local Path**: Browse to `c:\Users\User\Downloads\telegram_task_bot`
   - **Initialize with README**: Uncheck (you already have one)
   - **Git Ignore**: Python
   - **License**: MIT (or your choice)
4. Click **Create Repository**

#### Step 3: Review Changes
1. GitHub Desktop will show all files to be committed
2. **VERIFY** no sensitive files are included (check `.env`, `config/config.py`)
3. Uncheck any files you don't want to upload

#### Step 4: Make Initial Commit
1. In the "Summary" field, type: `Initial commit - Telegram Task Bot`
2. In the "Description" field (optional):
   ```
   AI-powered Telegram bot with:
   - Google Gemini LLM integration
   - Microsoft Outlook Tasks API
   - Natural language task creation
   - Modular architecture (Services, Handlers, Validators)
   ```
3. Click **Commit to main**

#### Step 5: Publish to GitHub
1. Click **Publish repository** (top right)
2. Choose:
   - **Name**: `telegram-task-bot`
   - **Description**: "AI-powered Telegram bot for Outlook task management with LLM integration"
   - **Keep this code private**: 
     - ✅ **Check this** if you want a private repo (recommended for portfolios)
     - ⬜ **Uncheck** if you want it public (open source)
3. Click **Publish Repository**

**✅ Done!** Your project is now on GitHub!

---

### Method 2: Command Line (Advanced)

#### Step 1: Initialize Git Repository
```powershell
cd c:\Users\User\Downloads\telegram_task_bot

# Initialize git (if not already done)
git init

# Check status
git status
```

#### Step 2: Create `.gitignore` (if needed)
```powershell
# The .gitignore content from section above should be in place
git status  # Verify .env and other secrets are NOT listed
```

#### Step 3: Stage Files for Commit
```powershell
# Stage all files
git add .

# OR stage specific files/folders
git add src/
git add docs/
git add README.md
git add requirements.txt
git add setup-env.ps1

# Verify what will be committed
git status
```

#### Step 4: Make Initial Commit
```powershell
git commit -m "Initial commit - Telegram Task Bot

AI-powered Telegram bot with:
- Google Gemini LLM integration
- Microsoft Outlook Tasks API
- Natural language task creation
- Modular architecture (Services, Handlers, Validators)"
```

#### Step 5: Create GitHub Repository
1. Go to [github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name**: `telegram-task-bot`
   - **Description**: "AI-powered Telegram bot for Outlook task management with LLM integration"
   - **Public/Private**: Choose based on your preference
   - **Don't initialize** with README, .gitignore, or license (you have them)
3. Click **Create repository**

#### Step 6: Link Local to GitHub
```powershell
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/telegram-task-bot.git

# Verify remote
git remote -v
```

#### Step 7: Push to GitHub
```powershell
# Push to main branch
git branch -M main
git push -u origin main
```

**✅ Done!** Your project is now on GitHub!

---

## 📝 Recommended: Create a Great README

Your `README.md` is the first thing people see. Enhance it with:

### Add Badges (Optional but Professional)
```markdown
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://telegram.org/)
```

### Add Screenshots/Demo
- Create a `screenshots/` folder
- Add images of your bot in action
- Reference them in README:
  ```markdown
  ## 📸 Screenshots
  ![Bot Demo](screenshots/demo.png)
  ```

### Add Architecture Diagram
- Use [Mermaid](https://mermaid.js.org/) for diagrams in README:
  ````markdown
  ## 🏗️ Architecture
  ```mermaid
  graph LR
      A[User] --> B[Telegram Bot]
      B --> C[LLM Service]
      B --> D[Outlook Service]
      C --> E[Google Gemini]
      D --> F[Microsoft Graph API]
  ```
  ````

---

## 🔒 Security Best Practices

### 1. Never Commit These Files:
- ✅ `.env` → Add to `.gitignore`
- ✅ `config/config.py` → Add to `.gitignore`
- ✅ `*.token` files → Add to `.gitignore`
- ✅ `bot.lock` → Add to `.gitignore`

### 2. Use Environment Variables
Ensure `config_template.py` has placeholders:
```python
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN_HERE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
```

### 3. Document Setup Without Exposing Secrets
In `SETUP.md`, provide instructions:
```markdown
## Environment Variables
Create a `.env` file (NOT committed to Git):
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
```
```

### 4. Scan for Accidentally Committed Secrets
Before pushing:
```powershell
# Search for potential secrets in staged files
git diff --cached | Select-String -Pattern "(AIza|sk-|xox|ghp_)" 
```

---

## 📁 Recommended Repository Structure

```
telegram-task-bot/
├── .github/               # GitHub-specific files
│   └── workflows/        # CI/CD workflows (optional)
├── docs/                 # Documentation
│   ├── SETUP.md
│   ├── API.md
│   ├── EXAMPLES.md
│   └── PHASE*.md
├── screenshots/          # Demo images (optional)
├── src/                  # Source code
│   ├── bot.py
│   ├── config/
│   ├── handlers/
│   ├── services/
│   ├── utils/
│   ├── validators/
│   └── formatters/
├── tests/                # Unit tests (optional)
├── .gitignore            # Git ignore rules
├── LICENSE               # License file
├── README.md             # Main documentation
├── requirements.txt      # Dependencies
└── setup-env.ps1         # Setup script
```

---

## 🎨 Make Your Repository Stand Out

### 1. Add a License
```powershell
# Create LICENSE file
# Use MIT, GPL, Apache 2.0, etc.
# Generator: https://choosealicense.com/
```

### 2. Add Topics/Tags
On GitHub repository page:
- Click ⚙️ (Settings gear) next to "About"
- Add topics: `telegram-bot`, `outlook-api`, `gemini-ai`, `python`, `task-management`, `microsoft-graph`

### 3. Write a Good Description
**Short version** (for GitHub "About"):
```
AI-powered Telegram bot integrating Google Gemini and Microsoft Outlook for intelligent task management
```

**Long version** (for README intro):
```markdown
# 🤖 Telegram Task Bot

An intelligent Telegram bot that converts natural language messages into 
Outlook tasks using Google's Gemini AI. Features modular architecture, 
Malaysia timezone support, and comprehensive error handling.

## ✨ Features
- 🧠 AI-powered intent detection (Google Gemini)
- 📝 Natural language task creation
- 📅 Smart due date parsing
- 🔗 Microsoft Outlook integration
- 🌏 Malaysia timezone (UTC+8) support
- ✅ Multi-layer validation
- 🏗️ Clean service-oriented architecture
```

### 4. Add Contributing Guidelines (Optional)
```markdown
## 🤝 Contributing
This is a portfolio/documentation project, but issues and suggestions are welcome!
```

---

## 🚀 After Upload: Next Steps

### 1. Verify Upload
- Visit `https://github.com/YOUR_USERNAME/telegram-task-bot`
- Check that:
  - ✅ README displays correctly
  - ✅ No `.env` or secret files visible
  - ✅ All documentation files present
  - ✅ Code is readable with syntax highlighting

### 2. Create a GitHub Pages Site (Optional)
Turn your documentation into a website:
1. Go to **Settings** → **Pages**
2. Source: **Deploy from branch** → **main** → **/docs**
3. Your docs will be at: `https://YOUR_USERNAME.github.io/telegram-task-bot/`

### 3. Add to Your Portfolio
Link from:
- LinkedIn projects section
- Personal website
- Resume/CV (GitHub link)

### 4. Keep It Updated
```powershell
# Make changes
git add .
git commit -m "Description of changes"
git push origin main
```

---

## 🆘 Common Issues

### Issue: "Permission denied (publickey)"
**Solution**: Set up SSH keys or use HTTPS with personal access token
```powershell
# Use HTTPS instead
git remote set-url origin https://github.com/YOUR_USERNAME/telegram-task-bot.git
```

### Issue: "Updates were rejected"
**Solution**: Pull first, then push
```powershell
git pull origin main --rebase
git push origin main
```

### Issue: Accidentally committed secrets
**Solution**: Remove from history (URGENT!)
```powershell
# Remove file from git history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch path/to/secret/file" --prune-empty --tag-name-filter cat -- --all

# Force push (BE CAREFUL!)
git push origin --force --all
```

Then **immediately**:
1. Change all exposed credentials
2. Rotate API keys
3. Update Telegram bot token

---

## ✅ Pre-Upload Checklist

Before you upload, verify:

- [ ] `.gitignore` file exists and includes `.env`, `config/config.py`, `*.lock`
- [ ] No secrets in code (search for `api_key`, `token`, `password`)
- [ ] `config_template.py` only has placeholder values
- [ ] README.md is complete and professional
- [ ] All documentation files are up-to-date
- [ ] License file added (if desired)
- [ ] Project description written
- [ ] Removed any test/temporary files
- [ ] Removed any personal information
- [ ] Requirements.txt is current (`pip freeze > requirements.txt`)

---

## 📚 Additional Resources

- [GitHub Docs: Create a Repo](https://docs.github.com/en/get-started/quickstart/create-a-repo)
- [GitHub Docs: Ignoring Files](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files)
- [Choose a License](https://choosealicense.com/)
- [Writing Good READMEs](https://readme.so/)
- [Markdown Guide](https://www.markdownguide.org/)

---

## 🎯 Quick Start Command Summary

```powershell
# Navigate to project
cd c:\Users\User\Downloads\telegram_task_bot

# Verify .gitignore is in place
cat .gitignore

# Initialize git
git init

# Stage files
git add .

# Check what will be committed
git status

# Make initial commit
git commit -m "Initial commit - Telegram Task Bot"

# Create repo on GitHub (via web), then:
git remote add origin https://github.com/YOUR_USERNAME/telegram-task-bot.git
git branch -M main
git push -u origin main
```

---

**Good luck with your GitHub upload! 🚀**

If you encounter any issues, check the Common Issues section or consult GitHub's documentation.
