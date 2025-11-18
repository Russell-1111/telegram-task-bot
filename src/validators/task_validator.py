"""
Task Validator for Summary and Input Validation

Validates task summaries against word count requirements and provides
fallback generation for invalid LLM-generated summaries.
"""
import logging
from dataclasses import dataclass
from typing import Set

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of validation with details
    
    Attributes:
        is_valid: Whether the validation passed
        word_count: Number of words in the validated string
        message: Human-readable validation message
        validated_value: Cleaned/processed value that was validated
    """
    is_valid: bool
    word_count: int
    message: str
    validated_value: str


@dataclass
class RelevanceValidationResult:
    """
    Result of input relevance validation
    
    Attributes:
        is_task_related: Whether the input appears to be task-related
        confidence: Confidence score (0.0-1.0)
        reason: Explanation for the classification
        detected_category: Category of input (task, greeting, question, random, etc.)
    """
    is_task_related: bool
    confidence: float
    reason: str
    detected_category: str


class TaskValidator:
    """
    Validates task summaries and related data.
    
    This validator ensures task summaries meet length requirements
    (typically 3-12 words) and provides fallback summary generation
    when LLM-generated summaries are invalid.
    
    Example:
        validator = TaskValidator(min_words=3, max_words=12)
        result = validator.validate_summary("Buy groceries tomorrow")
        
        if not result.is_valid:
            fallback = validator.generate_fallback_summary(original_message)
    """
    
    # Common stop words to filter out when generating fallback summaries
    DEFAULT_STOP_WORDS: Set[str] = {
        'i', 'me', 'to', 'a', 'an', 'the', 'and', 'or', 
        'but', 'in', 'on', 'at', 'by', 'for', 'with', 'from'
    }
    
    # Common task prefixes to remove
    TASK_PREFIXES = [
        'remind me to', 'i need to', 'i have to', 'i should',
        'please remind me to', 'task:', 'todo:', 'remember to'
    ]
    
    # Task-related action verbs and keywords
    TASK_ACTION_VERBS = {
        'buy', 'call', 'email', 'send', 'write', 'read', 'finish', 'complete',
        'submit', 'prepare', 'schedule', 'book', 'reserve', 'pay', 'order',
        'clean', 'organize', 'fix', 'repair', 'update', 'review', 'check',
        'create', 'make', 'build', 'develop', 'plan', 'attend', 'meet',
        'visit', 'contact', 'follow', 'research', 'study', 'practice',
        'cancel', 'renew', 'confirm', 'register', 'sign', 'file', 'draft',
        'remind', 'remember', 'pickup', 'deliver', 'ship', 'return'
    }
    
    # Task-related keywords that indicate task intent
    TASK_KEYWORDS = {
        'task', 'todo', 'reminder', 'appointment', 'meeting', 'deadline',
        'due', 'tomorrow', 'today', 'tonight', 'later', 'next', 'week',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    }
    
    # Greeting patterns
    GREETING_PATTERNS = {
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'good night', 'greetings', 'howdy', 'sup', 'yo', 'hola', 'bonjour'
    }
    
    # Question patterns
    QUESTION_PATTERNS = {
        'how are you', 'what is', 'what are', 'who is', 'who are', 'when is',
        'where is', 'why is', 'can you', 'could you', 'would you', 'will you',
        'do you', 'does', 'did you', 'have you', 'has', 'should i', 'tell me'
    }
    
    # Random/irrelevant patterns
    IRRELEVANT_PATTERNS = {
        'lol', 'lmao', 'haha', 'wow', 'cool', 'nice', 'ok', 'okay', 'yes', 'no',
        'thanks', 'thank you', 'bye', 'goodbye', 'see you', 'later', 'nevermind',
        'never mind', 'just kidding', 'jk', 'test', 'testing', 'hmm', 'uh', 'um'
    }
    
    def __init__(self, min_words: int = 3, max_words: int = 12):
        """
        Initialize the validator with word count limits
        
        Args:
            min_words: Minimum word count for valid summaries (default: 3)
            max_words: Maximum word count for valid summaries (default: 12)
        """
        if min_words > max_words:
            raise ValueError(
                f"min_words ({min_words}) cannot be greater than max_words ({max_words})"
            )
        
        self.min_words = min_words
        self.max_words = max_words
        self.stop_words = self.DEFAULT_STOP_WORDS.copy()
    
    def validate_input_relevance(self, user_input: str) -> RelevanceValidationResult:
        """
        Validate whether user input is task-related or irrelevant.
        
        This method uses keyword matching and pattern recognition to determine
        if the user's message describes an actual task vs. greetings, questions,
        or random comments.
        
        Args:
            user_input: The user's message to validate
            
        Returns:
            RelevanceValidationResult with classification details
        
        Examples:
            >>> validator.validate_input_relevance("Buy groceries tomorrow")
            RelevanceValidationResult(is_task_related=True, confidence=0.9, ...)
            
            >>> validator.validate_input_relevance("Hello, how are you?")
            RelevanceValidationResult(is_task_related=False, confidence=0.9, ...)
        """
        if not user_input or not isinstance(user_input, str):
            return RelevanceValidationResult(
                is_task_related=False,
                confidence=1.0,
                reason="Empty or invalid input",
                detected_category="invalid"
            )
        
        cleaned_input = user_input.strip().lower()
        words = cleaned_input.split()
        
        # Check for very short inputs (likely greetings or exclamations)
        if len(words) <= 2:
            # Check if it's a greeting (use word boundary matching)
            if any(f" {greeting} " in f" {cleaned_input} " or cleaned_input == greeting for greeting in self.GREETING_PATTERNS):
                return RelevanceValidationResult(
                    is_task_related=False,
                    confidence=0.95,
                    reason="Input is a greeting",
                    detected_category="greeting"
                )
            
            # Check if it's an irrelevant pattern (use word boundary matching)
            if any(f" {pattern} " in f" {cleaned_input} " or cleaned_input == pattern for pattern in self.IRRELEVANT_PATTERNS):
                return RelevanceValidationResult(
                    is_task_related=False,
                    confidence=0.9,
                    reason="Input is a common irrelevant phrase",
                    detected_category="irrelevant"
                )
        
        # Score-based detection
        task_score = 0.0
        reasons = []
        
        # Check for task action verbs (strong indicator)
        action_verbs_found = [word for word in words if word in self.TASK_ACTION_VERBS]
        if action_verbs_found:
            task_score += 0.4
            reasons.append(f"Contains action verbs: {', '.join(action_verbs_found)}")
        
        # Check for task keywords
        task_keywords_found = [word for word in words if word in self.TASK_KEYWORDS]
        if task_keywords_found:
            task_score += 0.3
            reasons.append(f"Contains task keywords: {', '.join(task_keywords_found)}")
        
        # Check for task prefixes (strong indicator)
        for prefix in self.TASK_PREFIXES:
            if cleaned_input.startswith(prefix):
                task_score += 0.5
                reasons.append(f"Starts with task prefix: '{prefix}'")
                break
        
        # Check for greetings (negative indicator)
        # Use word boundary matching to avoid false positives
        greetings_found = [g for g in self.GREETING_PATTERNS if f" {g} " in f" {cleaned_input} " or cleaned_input == g]
        if greetings_found:
            task_score -= 0.5
            reasons.append(f"Contains greeting: {', '.join(greetings_found)}")
        
        # Check for question patterns (negative indicator)
        # Use word boundary matching to avoid false positives
        questions_found = [q for q in self.QUESTION_PATTERNS if f" {q} " in f" {cleaned_input} " or cleaned_input == q]
        if questions_found:
            task_score -= 0.4
            reasons.append(f"Contains question pattern: {', '.join(questions_found)}")
        
        # Check if it ends with a question mark
        if user_input.strip().endswith('?'):
            task_score -= 0.3
            reasons.append("Ends with question mark")
        
        # Check for irrelevant patterns (negative indicator)
        # Use word boundary matching to avoid false positives (e.g., "no" in "economics")
        irrelevant_found = [p for p in self.IRRELEVANT_PATTERNS if f" {p} " in f" {cleaned_input} " or cleaned_input == p]
        if irrelevant_found:
            task_score -= 0.3
            reasons.append(f"Contains irrelevant pattern: {', '.join(irrelevant_found)}")
        
        # Determine classification
        is_task_related = task_score > 0.2
        confidence = min(abs(task_score), 1.0)
        
        # Determine category
        if task_score > 0.2:
            detected_category = "task"
        elif greetings_found:
            detected_category = "greeting"
        elif questions_found or user_input.strip().endswith('?'):
            detected_category = "question"
        elif irrelevant_found:
            detected_category = "irrelevant"
        else:
            detected_category = "unclear"
        
        reason_text = "; ".join(reasons) if reasons else "No clear indicators found"
        
        return RelevanceValidationResult(
            is_task_related=is_task_related,
            confidence=confidence,
            reason=reason_text,
            detected_category=detected_category
        )
    
    def validate_summary(self, summary: str) -> ValidationResult:
        """
        Validate task summary meets word count requirements
        
        Args:
            summary: The task summary to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        if not summary or not isinstance(summary, str):
            return ValidationResult(
                is_valid=False,
                word_count=0,
                message='Summary is empty or not a string',
                validated_value=''
            )
        
        # Clean and tokenize the summary
        cleaned = ' '.join(summary.strip().split())  # Remove extra whitespace
        words = cleaned.split()
        word_count = len(words)
        
        if word_count < self.min_words:
            return ValidationResult(
                is_valid=False,
                word_count=word_count,
                message=f'Summary too short: {word_count} words (minimum: {self.min_words})',
                validated_value=cleaned
            )
        elif word_count > self.max_words:
            return ValidationResult(
                is_valid=False,
                word_count=word_count,
                message=f'Summary too long: {word_count} words (maximum: {self.max_words})',
                validated_value=cleaned
            )
        
        return ValidationResult(
            is_valid=True,
            word_count=word_count,
            message=f'Valid summary: {word_count} words',
            validated_value=cleaned
        )
    
    def generate_fallback_summary(self, user_message: str) -> str:
        """
        Generate a fallback summary from user message if LLM summary is invalid.
        
        This method attempts to extract meaningful words from the user's message
        and create a valid summary within word count limits.
        
        Args:
            user_message: Original user message
            
        Returns:
            A valid task summary within word limits
        """
        if not user_message or not isinstance(user_message, str):
            return "Unknown task"
        
        # Step 1: Remove common task prefixes
        cleaned_message = self._remove_task_prefixes(user_message)
        
        # Step 2: Extract meaningful words (filter stop words)
        meaningful_words = self._extract_meaningful_words(cleaned_message)
        
        # Step 3: Create summary within word limits
        if len(meaningful_words) >= self.min_words:
            # Truncate if too long
            if len(meaningful_words) > self.max_words:
                return ' '.join(meaningful_words[:self.max_words])
            return ' '.join(meaningful_words)
        
        # Step 4: Fallback - use first N words of cleaned message
        fallback_words = cleaned_message.split()
        if len(fallback_words) >= self.min_words:
            return ' '.join(fallback_words[:self.max_words])
        
        # Ultimate fallback
        first_words = user_message.split()[:self.max_words]
        if len(first_words) >= self.min_words:
            return ' '.join(first_words)
        
        return f"Task: {user_message[:30]}"  # Last resort
    
    def _remove_task_prefixes(self, message: str) -> str:
        """Remove common task prefixes from message"""
        message_lower = message.lower()
        
        for prefix in self.TASK_PREFIXES:
            if message_lower.startswith(prefix):
                return message[len(prefix):].strip()
        
        return message
    
    def _extract_meaningful_words(self, message: str) -> list[str]:
        """
        Extract meaningful words by filtering stop words and punctuation
        
        Args:
            message: Message to extract words from
            
        Returns:
            List of meaningful words
        """
        words = message.split()
        meaningful_words = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?;:').lower()
            
            # Keep word if it's not a stop word and has sufficient length
            if clean_word not in self.stop_words and len(clean_word) > 2:
                meaningful_words.append(word.strip('.,!?;:'))
        
        return meaningful_words
