"""
Test script to validate the two main fixes:
1. 12-word summary truncation (instead of 8)
2. Input relevance validation (reject irrelevant inputs)

This script tests the validators and services without requiring Telegram or Outlook API.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from validators.task_validator import TaskValidator, RelevanceValidationResult
from services.llm_service import TaskIntent

def test_summary_truncation():
    """Test that fallback summaries are truncated to 12 words, not 8"""
    print("\n" + "="*70)
    print("TEST 1: Summary Truncation (12-word limit)")
    print("="*70)
    
    # Create a validator
    validator = TaskValidator(min_words=3, max_words=12)
    
    # Test case: Long message that needs truncation
    long_message = "I need to buy groceries milk eggs bread butter cheese and also some vegetables fruits and meat products"
    
    # Generate fallback summary
    fallback_summary = validator.generate_fallback_summary(long_message)
    word_count = len(fallback_summary.split())
    
    print(f"\nOriginal message ({len(long_message.split())} words):")
    print(f"  '{long_message}'")
    print(f"\nFallback summary ({word_count} words):")
    print(f"  '{fallback_summary}'")
    
    # Validate it's within limits
    validation = validator.validate_summary(fallback_summary)
    print(f"\nValidation result:")
    print(f"  Valid: {validation.is_valid}")
    print(f"  Word count: {validation.word_count}")
    print(f"  Message: {validation.message}")
    
    if validation.is_valid and validation.word_count <= 12:
        print("\n✅ PASS: Summary is properly truncated to 12 words or less")
        return True
    else:
        print("\n❌ FAIL: Summary exceeds 12 words or is invalid")
        return False


def test_input_relevance_validation():
    """Test that irrelevant inputs are properly detected"""
    print("\n" + "="*70)
    print("TEST 2: Input Relevance Validation")
    print("="*70)
    
    validator = TaskValidator()
    
    # Test cases: (input, expected_is_task_related, description)
    test_cases = [
        # Task-related inputs (should be accepted)
        ("Buy groceries tomorrow", True, "Task with action verb"),
        ("Call dentist on Friday", True, "Task with specific action"),
        ("Remind me to submit report", True, "Task with 'remind me' prefix"),
        ("Complete project proposal by next week", True, "Task with deadline"),
        ("Schedule meeting with team", True, "Task with scheduling"),
        
        # Greetings (should be rejected)
        ("Hello", False, "Simple greeting"),
        ("Hi there", False, "Casual greeting"),
        ("Good morning", False, "Time-based greeting"),
        
        # Questions (should be rejected)
        ("How are you?", False, "Question about wellbeing"),
        ("What time is it?", False, "Question about time"),
        ("Can you help me?", False, "Question seeking help"),
        
        # Irrelevant/random (should be rejected)
        ("Thanks", False, "Gratitude expression"),
        ("lol", False, "Casual expression"),
        ("ok", False, "Acknowledgment"),
        ("testing", False, "Test message"),
        ("just checking if this works", False, "Random comment"),
    ]
    
    passed = 0
    failed = 0
    
    for user_input, expected_task, description in test_cases:
        result = validator.validate_input_relevance(user_input)
        
        status = "✅" if result.is_task_related == expected_task else "❌"
        if result.is_task_related == expected_task:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} {description}")
        print(f"  Input: '{user_input}'")
        print(f"  Expected: {'Task' if expected_task else 'Non-task'}")
        print(f"  Got: {'Task' if result.is_task_related else 'Non-task'}")
        print(f"  Category: {result.detected_category}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reason: {result.reason}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'='*70}")
    
    return failed == 0


def test_summary_validation():
    """Test that summary validation works correctly"""
    print("\n" + "="*70)
    print("TEST 3: Summary Validation (3-12 word range)")
    print("="*70)
    
    validator = TaskValidator(min_words=3, max_words=12)
    
    test_cases = [
        ("Buy groceries", False, "Too short (2 words)"),
        ("Buy groceries tomorrow", True, "Valid (3 words)"),
        ("Buy groceries and milk", True, "Valid (4 words)"),
        ("Call mom about dinner plans tonight", True, "Valid (6 words)"),
        ("Schedule important team meeting for next Monday morning session", True, "Valid (9 words)"),
        ("Complete project proposal document and submit to manager by Friday afternoon", True, "Valid (11 words - within max of 12)"),
        ("This is a very very long task summary that definitely exceeds the maximum allowed word count", False, "Too long (16 words)"),
        ("", False, "Empty string"),
    ]
    
    passed = 0
    failed = 0
    
    for summary, expected_valid, description in test_cases:
        result = validator.validate_summary(summary)
        
        status = "✅" if result.is_valid == expected_valid else "❌"
        if result.is_valid == expected_valid:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} {description}")
        print(f"  Summary: '{summary}'")
        print(f"  Expected: {'Valid' if expected_valid else 'Invalid'}")
        print(f"  Got: {'Valid' if result.is_valid else 'Invalid'}")
        print(f"  Word count: {result.word_count}")
        print(f"  Message: {result.message}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'='*70}")
    
    return failed == 0


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE FIX VALIDATION TEST SUITE")
    print("="*70)
    print("\nTesting fixes for:")
    print("  1. 12-word summary truncation (previously 8)")
    print("  2. Input relevance validation (reject non-task inputs)")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Summary Truncation", test_summary_truncation()))
    results.append(("Input Relevance Validation", test_input_relevance_validation()))
    results.append(("Summary Validation", test_summary_validation()))
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Both fixes are working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
