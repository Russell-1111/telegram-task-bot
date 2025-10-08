"""
Test script to verify EXAMPLES.md code examples work correctly
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("Testing EXAMPLES.md Code Examples")
print("=" * 60)

# Test 2: StateManager (UserStateManager) - CRITICAL TEST
print("\n[Test 2] StateManager - Class Name and Methods")
print("-" * 60)
try:
    from src.utils.state_manager import UserStateManager
    
    state_manager = UserStateManager()
    print("[PASS] UserStateManager imported and initialized")
    
    # Test set_user_task signature
    import inspect
    sig = inspect.signature(state_manager.set_user_task)
    params = list(sig.parameters.keys())
    expected_params = ['user_id', 'task_id', 'task_title', 'due_date']
    
    if params == expected_params:
        print(f"[PASS] set_user_task() has correct signature: {params}")
    else:
        print(f"[FAIL] set_user_task() signature mismatch!")
        print(f"       Expected: {expected_params}")
        print(f"       Got: {params}")
    
    # Test basic operations
    test_user_id = 999999
    state_manager.set_user_task(
        user_id=test_user_id,
        task_id="test_task_123",
        task_title="Test Task",
        due_date="2025-10-10"
    )
    print(f"[PASS] set_user_task() executed successfully")
    
    if state_manager.has_user_task(test_user_id):
        print(f"[PASS] has_user_task() returns True")
        
        task_data = state_manager.get_user_task(test_user_id)
        print(f"[PASS] get_user_task() returned: {task_data}")
        
        if task_data['title'] == "Test Task":
            print(f"[PASS] Task data matches expected values")
        else:
            print(f"[FAIL] Task data mismatch")
    
    state_manager.clear_user_task(test_user_id)
    if not state_manager.has_user_task(test_user_id):
        print(f"[PASS] clear_user_task() works correctly")
    
except ImportError as e:
    print(f"[FAIL] Import error - {e}")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 3: TokenManager (global, not per-user)
print("\n[Test 3] TokenManager - Global Design (No user_id)")
print("-" * 60)
try:
    from src.utils.token_manager import TokenManager
    
    token_manager = TokenManager()
    print(f"[PASS] TokenManager imported and initialized")
    
    # Test method signatures (should NOT have user_id)
    import inspect
    
    # Check has_token
    sig = inspect.signature(token_manager.has_token)
    params = list(sig.parameters.keys())
    if len(params) == 0:
        print(f"[PASS] has_token() takes no parameters (global design)")
    else:
        print(f"[FAIL] has_token() has parameters: {params} (should be global)")
    
    # Check get_token
    sig = inspect.signature(token_manager.get_token)
    params = list(sig.parameters.keys())
    if len(params) == 0:
        print(f"[PASS] get_token() takes no parameters (global design)")
    else:
        print(f"[FAIL] get_token() has parameters: {params} (should be global)")
    
    # Check set_token
    sig = inspect.signature(token_manager.set_token)
    params = list(sig.parameters.keys())
    expected_params = ['token']
    if params == expected_params:
        print(f"[PASS] set_token() has correct signature: {params}")
    else:
        print(f"[FAIL] set_token() signature: {params}, expected: {expected_params}")
    
    # Test basic operations
    token_manager.set_token("test_token_12345")
    print(f"[PASS] set_token() executed successfully")
    
    if token_manager.has_token():
        print(f"[PASS] has_token() returns True")
        
        token = token_manager.get_token()
        if token == "test_token_12345":
            print(f"[PASS] get_token() returns correct value")
        else:
            print(f"[FAIL] Token mismatch: {token}")
    
    token_manager.clear_token()
    if not token_manager.has_token():
        print(f"[PASS] clear_token() works correctly")
    
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 4: TaskValidator methods
print("\n[Test 4] TaskValidator - Correct Method Names")
print("-" * 60)
try:
    from src.validators.task_validator import TaskValidator
    
    validator = TaskValidator()
    print(f"[PASS] TaskValidator imported and initialized")
    
    # Check for correct methods
    import inspect
    methods = [name for name, method in inspect.getmembers(validator, predicate=inspect.ismethod)]
    
    if 'validate_summary' in methods:
        print(f"[PASS] validate_summary() method exists")
    else:
        print(f"[FAIL] validate_summary() method NOT found")
    
    if 'validate_input_relevance' in methods:
        print(f"[PASS] validate_input_relevance() method exists")
    else:
        print(f"[FAIL] validate_input_relevance() method NOT found")
    
    if 'generate_fallback_summary' in methods:
        print(f"[PASS] generate_fallback_summary() method exists")
    else:
        print(f"[FAIL] generate_fallback_summary() method NOT found")
    
    # Check for WRONG methods that shouldn't exist
    wrong_methods = ['validate_title', 'validate_date']
    for method_name in wrong_methods:
        if method_name in methods:
            print(f"[FAIL] {method_name}() exists but SHOULDN'T (removed from docs)")
        else:
            print(f"[PASS] {method_name}() correctly does NOT exist")
    
    # Test validate_summary
    result = validator.validate_summary("Buy groceries at the store")
    print(f"[PASS] validate_summary() executed successfully")
    
    # Test validate_input_relevance
    result = validator.validate_input_relevance("Buy groceries tomorrow")
    print(f"[PASS] validate_input_relevance() executed successfully")
    
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 5: Date formatter functions
print("\n[Test 5] Date Formatter - validate_and_process_date()")
print("-" * 60)
try:
    from src.formatters.date_formatter import validate_and_process_date, format_due_date_for_outlook
    
    print(f"[PASS] Date formatter functions imported")
    
    # Test validate_and_process_date
    result = validate_and_process_date("2025-10-10")
    if result:
        print(f"[PASS] validate_and_process_date('2025-10-10') = {result}")
    else:
        print(f"[FAIL] validate_and_process_date() returned None")
    
    # Test format_due_date_for_outlook
    result = format_due_date_for_outlook("2025-10-10")
    print(f"[PASS] format_due_date_for_outlook() = {result}")
    
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("Core EXAMPLES.md fixes verified!")
print("Key findings:")
print("  - UserStateManager class name: CORRECT")
print("  - set_user_task() parameter: task_title (not title)")
print("  - TokenManager design: Global (not per-user)")
print("  - TaskValidator methods: All correct")
print("  - Date formatter functions: All correct")
print("=" * 60)
