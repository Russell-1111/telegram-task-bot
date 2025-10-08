# 🚀 GitHub Upload Checklist - Telegram Task Bot

**Last Updated:** October 8, 2025  
**Status:** 🔴 **CRITICAL SECURITY STEP REQUIRED**

---

## ⚠️ URGENT: Security Pre-Flight (DO THIS FIRST!)

### 🔴 Step 1: Remove .env from Staging (CRITICAL!)

```powershell
git restore --staged .env
```

**Why?** Your `.env` file contains actual API keys and secrets. If pushed to GitHub, they'll be publicly exposed!

**Verification:**
```powershell
git status
# .env should appear under "Untracked files" or NOT appear at all
```

---

## ✅ Quick Upload Checklist

### Pre-Push Security Checks

- [ ] **CRITICAL:** `.env` is NOT staged (`git status` should NOT show it under "Changes to be committed")
- [ ] **CRITICAL:** No hardcoded secrets in source code
  ```powershell
  Select-String -Path "src\**\*.py" -Pattern "(AIza|sk-|xox|ghp_)" -CaseSensitive
  ```
- [ ] `.env.template` exists with placeholder values
- [ ] `.gitignore` includes `.env` and `.venv/`
- [ ] Remove `__pycache__/` from staging:
  ```powershell
  git restore --staged **/__pycache__/
  git restore --staged bot.lock
  ```

### Repository Setup (GitHub Website)

- [ ] Go to https://github.com/new
- [ ] Repository name: `telegram-task-bot` (or your choice)
- [ ] Description: "AI-powered Telegram bot for Outlook task management"
- [ ] Visibility: **PRIVATE** recommended (personal project)
- [ ] Do NOT initialize with README (you have one)
- [ ] Add license: MIT recommended

### Local Repository Preparation

- [ ] Review staged files: `git status`
- [ ] Review changes: `git diff --staged`
- [ ] Commit with descriptive message:
  ```powershell
  git commit -m "Initial commit: Telegram Task Bot with Outlook integration"
  ```

### Push to GitHub

- [ ] Add remote (replace YOUR-USERNAME):
  ```powershell
  git remote add origin https://github.com/YOUR-USERNAME/telegram-task-bot.git
  ```
- [ ] Verify remote: `git remote -v`
- [ ] Push to GitHub: `git push -u origin main`

### Post-Push Verification

- [ ] Visit repository: `https://github.com/YOUR-USERNAME/telegram-task-bot`
- [ ] Verify `.env` is NOT visible
- [ ] Verify documentation displays correctly
- [ ] Verify source code is organized
- [ ] Add repository topics: `telegram-bot`, `python`, `outlook-api`, `google-gemini`

---

## 🔍 Quick Security Scan

```powershell
# Check .gitignore is working
git check-ignore .env
# Expected: .env

# Verify .env is NOT tracked
git ls-files | Select-String ".env"
# Expected: NO output (only .env.template should appear)

# Scan for secrets in tracked files
Select-String -Path "src\**\*.py" -Pattern "(AIza|sk-|xox|ghp_|Bot.*[0-9]{10}:)" -CaseSensitive
# Expected: NO matches
```

---

## 📋 Files to Upload vs Keep Local

### ✅ Upload (Public Documentation)
- README.md, SETUP.md, API.md, EXAMPLES.md
- All `docs/*.md` files
- All `src/**/*.py` source code
- `.env.template` (template only!)
- `requirements.txt`, `.gitignore`
- `scripts/` (git helpers)

### ❌ Keep Local (Secrets & Runtime)
- `.env` (YOUR secrets!)
- `.venv/` (virtual environment)
- `__pycache__/` (Python cache)
- `bot.lock` (runtime lock)
- `*.log` files
- `.msal_token_cache.json` (OAuth tokens)

---

## 🚨 Emergency: If You Pushed Secrets

1. **IMMEDIATELY** revoke all API keys:
   - Telegram: @BotFather → regenerate token
   - Gemini: https://aistudio.google.com/app/apikey → delete key
   - Azure: Rotate client secrets

2. **Remove from Git history:**
   ```powershell
   git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
   git push origin --force --all
   ```

3. **Contact GitHub Support** to report exposed secrets

---

## ✅ Success Criteria

- ✅ Repository visible on GitHub
- ✅ README displays correctly
- ✅ No `.env` file visible
- ✅ No API keys in any files
- ✅ Documentation renders properly
- ✅ License file present

---

**For detailed instructions, see [`GITHUB-UPLOAD-GUIDE.md`](GITHUB-UPLOAD-GUIDE.md)**

**Ready?** Start with the CRITICAL security step above! 🔒