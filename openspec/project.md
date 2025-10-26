# Project Context

## Purpose
Telegram Task Bot with Outlook Integration - A bot that helps users manage their Outlook tasks through natural language conversation via Telegram.

## Tech Stack
- Python 3.x
- python-telegram-bot (Telegram API)
- Microsoft Graph API (Outlook integration)
- OpenAI API (LLM for natural language processing)
- pytest (Testing)

## Project Conventions

### Code Style
- PEP 8 compliant Python code
- Type hints preferred
- Docstrings for all public functions/classes
- Module-level organization under `src/`

### Architecture Patterns
- Service layer pattern (`src/services/`)
- Handler pattern for Telegram commands/messages (`src/handlers/`)
- Utility modules for cross-cutting concerns (`src/utils/`)
- Separation of API logic (`outlook_api.py` wraps Graph API, `OutlookService` provides higher-level interface)

### Testing Strategy
- pytest for unit tests (in `tests/` directory)
- Test files mirror source structure
- Coverage reporting with pytest-cov
- Integration tests for critical flows

### Git Workflow
- Main branch for stable code
- Feature branches for new work (e.g., `cleanup/remove-redundant-code`)
- Commit messages follow conventional commits style

## Domain Context
- Users interact via Telegram chat
- Bot processes natural language to create/manage Outlook tasks
- LLM (OpenAI) parses user intent from messages
- Tasks sync with Microsoft Outlook via Graph API
- State management for multi-step task creation flows

## Important Constraints
- Must handle Microsoft authentication tokens securely
- API rate limits for both Telegram and Graph API
- LLM token costs need optimization
- Bot must handle concurrent users safely (lock manager)

## External Dependencies
- Telegram Bot API
- Microsoft Graph API
- OpenAI API
- Python packages in requirements.txt
