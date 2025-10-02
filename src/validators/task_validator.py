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
    
    def test_validation(self):
        """
        Test function to verify summary validation works correctly.
        Useful for development and debugging.
        """
        test_cases = [
            ("Buy groceries", False, "Too short (2 words)"),
            ("Buy groceries and milk", True, "Valid (4 words)"),
            ("Call mom about dinner plans tonight", True, "Valid (6 words)"),
            ("This is a very very long task summary that exceeds the maximum", False, "Too long"),
            ("", False, "Empty string"),
        ]
        
        logger.info("Running validation tests...")
        
        for summary, expected_valid, description in test_cases:
            result = self.validate_summary(summary)
            status = "✅" if result.is_valid == expected_valid else "❌"
            logger.info(f"{status} {description}: '{summary}' -> {result.message}")
        
        logger.info("Validation tests complete")
