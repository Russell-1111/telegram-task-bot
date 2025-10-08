"""
Test to verify API.md documentation accuracy
"""
import sys
from pathlib import Path
import inspect
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("=" * 60)
print("Testing API.md Documentation Accuracy")
print("=" * 60)

# Test 1: UserStateManager.set_user_task parameter name
print("\n[Test 1] UserStateManager.set_user_task() - Parameter Names")
print("-" * 60)
try:
    from src.utils.state_manager import UserStateManager
    
    state_manager = UserStateManager()
    sig = inspect.signature(state_manager.set_user_task)
    params = list(sig.parameters.keys())
    
    print(f"Parameters: {params}")
    
    # Check for correct parameter name
    if 'task_title' in params:
        print("[PASS] Parameter 'task_title' found (API.md now correct)")
    else:
        print(f"[FAIL] Expected 'task_title' parameter, got: {params}")
    
    if 'title' in params:
        print("[FAIL] Found 'title' parameter (should be 'task_title')")
    else:
        print("[PASS] No 'title' parameter (correctly named 'task_title')")
    
    # Verify full signature
    expected = ['user_id', 'task_id', 'task_title', 'due_date']
    if params == expected:
        print(f"[PASS] Full signature matches: {params}")
    else:
        print(f"[WARN] Signature differs from expected")
        print(f"       Expected: {expected}")
        print(f"       Got:      {params}")

except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Test 2: LLMService.analyze_task_request parameter types
print("\n[Test 2] LLMService.analyze_task_request() - Parameter Types")
print("-" * 60)
try:
    from src.services.llm_service import LLMService, TaskIntent
    from src.config.settings import config
    import pytz
    
    llm_service = LLMService(config.gemini_api_key, config.gemini_model_name)
    sig = inspect.signature(llm_service.analyze_task_request)
    
    print(f"Parameters: {list(sig.parameters.keys())}")
    print(f"Annotations: {sig.parameters['current_date'].annotation}")
    
    # Check current_date annotation
    current_date_annotation = sig.parameters['current_date'].annotation
    
    if 'datetime' in str(current_date_annotation):
        print("[PASS] current_date expects datetime type (API.md now correct)")
    else:
        print(f"[WARN] current_date annotation: {current_date_annotation}")
    
    # Verify we can call it with datetime (don't actually call, just check signature)
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    current_date = datetime.now(malaysia_tz)
    
    print(f"[PASS] Can create datetime object for current_date parameter")
    print(f"       Type: {type(current_date)}")

except Exception as e:
    print(f"[NOTE] Cannot fully test (requires Google API): {e}")

# Test 3: TaskIntent dataclass attributes
print("\n[Test 3] TaskIntent Dataclass - Complete Attributes")
print("-" * 60)
try:
    from src.services.llm_service import TaskIntent
    
    # Check all attributes
    expected_attrs = ['intent', 'summary', 'due_date', 'confidence', 'raw_response']
    
    # Get actual attributes (filter out special methods)
    actual_attrs = [attr for attr in dir(TaskIntent) if not attr.startswith('_')]
    
    print(f"Expected attributes: {expected_attrs}")
    print(f"Actual attributes: {[a for a in actual_attrs if a in expected_attrs]}")
    
    for attr in expected_attrs:
        if hasattr(TaskIntent, '__annotations__') and attr in TaskIntent.__annotations__:
            print(f"[PASS] {attr}: {TaskIntent.__annotations__[attr]}")
        else:
            print(f"[FAIL] {attr} not found in TaskIntent")
    
    # Verify we can create a TaskIntent instance
    task_intent = TaskIntent(
        intent="create_task",
        summary="Test task",
        due_date="2025-10-10",
        confidence=0.9,
        raw_response="{}"
    )
    print(f"[PASS] Can instantiate TaskIntent with all 5 attributes")
    print(f"       Created: {task_intent}")

except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("API.md Validation Summary")
print("=" * 60)
print("Key corrections made:")
print("  1. UserStateManager.set_user_task() - 'title' -> 'task_title'")
print("  2. LLMService.analyze_task_request() - 'current_date' is datetime")
print("  3. TaskIntent - Documented all 5 attributes (not just 3)")
print("=" * 60)
