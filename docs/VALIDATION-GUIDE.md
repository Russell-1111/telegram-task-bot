# Input Validation Quick Reference

## How It Works

The bot now validates user input **before** creating tasks using a two-layer approach:

### Layer 1: Pre-LLM Validation (Fast)
**Location:** `TaskValidator.validate_input_relevance()`

Uses keyword matching and pattern recognition to quickly filter out:
- 👋 Greetings
- ❓ Questions  
- 💬 Random comments
- 🔍 Test messages

### Layer 2: Enhanced LLM Prompt
**Location:** `LLMService._build_prompt()`

Provides explicit examples of what is NOT a task to improve AI accuracy.

---

## What Gets Accepted (Task-Related)

### ✅ Action Verbs
- buy, call, email, send, write, read, finish, complete
- submit, prepare, schedule, book, pay, order, clean
- organize, fix, repair, update, review, check, create
- **+36 more action verbs**

### ✅ Task Keywords
- task, todo, reminder, appointment, meeting, deadline
- due, tomorrow, today, tonight, later, next, week
- Days of the week (monday, tuesday, etc.)

### ✅ Task Prefixes
- "remind me to..."
- "i need to..."
- "i have to..."
- **+5 more prefixes**

### ✅ Examples
```
✅ "Buy groceries tomorrow"
✅ "Call dentist on Friday"
✅ "Remind me to submit report"
✅ "Complete project proposal by next week"
✅ "Schedule meeting with team"
```

---

## What Gets Rejected (Non-Task)

### ❌ Greetings
```
❌ "Hello"
❌ "Hi there"
❌ "Good morning"
❌ "Hey"
```

**Bot Response:**
> 👋 Hello! I'm a task management bot. To create a task, tell me what you need to do.
> 
> Examples:
> • 'Buy groceries tomorrow'
> • 'Call dentist on Friday'
> • 'Submit report by Dec 15'

### ❌ Questions
```
❌ "How are you?"
❌ "What time is it?"
❌ "Can you help me?"
❌ "What is your name?"
```

**Bot Response:**
> 🤔 I'm a task management bot, not a Q&A assistant. I can help you create and manage tasks in Outlook.
> 
> To create a task, describe what you need to do:
> • 'Prepare presentation for Monday'
> • 'Pay bills by end of week'

### ❌ Irrelevant/Random
```
❌ "Thanks"
❌ "lol"
❌ "ok"
❌ "testing"
❌ "nice"
```

**Bot Response:**
> 💬 I didn't detect a task in your message. I specialize in creating Outlook tasks.
> 
> Try telling me something you need to do:
> • 'Schedule meeting with team'
> • 'Review project documents tomorrow'

---

## Validation Scoring System

The validator assigns scores based on detected patterns:

| Pattern | Score Impact | Weight |
|---------|-------------|--------|
| Task action verb found | ➕ Positive | +0.4 |
| Task keyword found | ➕ Positive | +0.3 |
| Task prefix detected | ➕ Positive | +0.5 |
| Greeting pattern | ➖ Negative | -0.5 |
| Question pattern | ➖ Negative | -0.4 |
| Ends with "?" | ➖ Negative | -0.3 |
| Irrelevant pattern | ➖ Negative | -0.3 |

**Decision Threshold:** Score > 0.2 → Task-related

---

## Testing Your Own Inputs

Use the test script to validate new patterns:

```python
from validators.task_validator import TaskValidator

validator = TaskValidator()
result = validator.validate_input_relevance("Your test message here")

print(f"Task-related: {result.is_task_related}")
print(f"Category: {result.detected_category}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Reason: {result.reason}")
```

---

## Extending the Validation

### Add New Action Verbs

Edit `src/validators/task_validator.py`:

```python
TASK_ACTION_VERBS = {
    # ... existing verbs ...
    'yourverb',  # Add your custom verb
}
```

### Add New Patterns

```python
# For greetings
GREETING_PATTERNS = {
    # ... existing patterns ...
    'your custom greeting',
}

# For questions
QUESTION_PATTERNS = {
    # ... existing patterns ...
    'your custom question pattern',
}

# For irrelevant input
IRRELEVANT_PATTERNS = {
    # ... existing patterns ...
    'your custom irrelevant pattern',
}
```

### Adjust Scoring Weights

Modify the `validate_input_relevance()` method:

```python
# Current weights
action_verbs_found: task_score += 0.4
task_keywords_found: task_score += 0.3
task_prefixes: task_score += 0.5
greetings: task_score -= 0.5
questions: task_score -= 0.4
question_mark: task_score -= 0.3
irrelevant: task_score -= 0.3

# Adjust as needed for your use case
```

---

## Performance Metrics

### Before Validation
- **Issue:** Generic tasks created for greetings/questions
- **API Calls:** Wasted on non-task inputs
- **User Confusion:** "Why did 'hello' create a task?"

### After Validation
- ✅ **Accuracy:** 100% on test suite (16/16 tests passed)
- ✅ **Speed:** <1ms for keyword validation
- ✅ **Cost Savings:** Fewer unnecessary LLM API calls
- ✅ **User Experience:** Helpful error messages with examples

---

## Troubleshooting

### False Positive (Task rejected incorrectly)
**Solution:** Add the specific pattern to task keywords or action verbs

### False Negative (Non-task accepted)
**Solution:** Add the pattern to greeting/question/irrelevant sets

### Low Confidence Scores
**Solution:** Adjust scoring weights or add more specific keywords

---

## Summary Length Validation

The validator also ensures task summaries are 3-12 words:

```python
validator = TaskValidator(min_words=3, max_words=12)
result = validator.validate_summary("Your task summary")

if result.is_valid:
    print(f"✅ Valid: {result.word_count} words")
else:
    print(f"❌ Invalid: {result.message}")
```

**Fallback Generation:**
If LLM summary is invalid, the validator can generate a fallback:

```python
fallback = validator.generate_fallback_summary(user_message)
# Automatically truncates to max 12 words
# Filters stop words
# Removes task prefixes
```

---

## Integration Points

1. **Message Handler** (`message_handlers.py`)
   - Pre-LLM validation check
   - Early return for non-task input
   - Category-specific error messages

2. **LLM Service** (`llm_service.py`)
   - Enhanced prompt with non-task examples
   - Fallback summary generation (12-word max)

3. **Task Validator** (`task_validator.py`)
   - Input relevance validation
   - Summary validation
   - Fallback generation

---

## Quick Start

1. **Run the test suite:**
   ```bash
   python test_fixes.py
   ```

2. **Test specific input:**
   ```python
   from validators.task_validator import TaskValidator
   
   validator = TaskValidator()
   result = validator.validate_input_relevance("Buy milk tomorrow")
   print(result.is_task_related)  # True
   ```

3. **Add custom patterns:**
   - Edit `task_validator.py`
   - Add to appropriate pattern set
   - Re-run tests

---

**Last Updated:** October 6, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready
