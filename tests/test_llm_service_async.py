"""
Unit and Integration Tests for Async LLM Service

Tests cover:
- Async analyze_task_request method with asyncio.to_thread mocking
- Non-blocking concurrent request handling
- Error handling preserves async behavior
- Fallback intent generation during failures
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytz

from services.llm_service import LLMService, TaskIntent


MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


class TestAsyncLLMService:
    """Unit tests for async LLMService methods."""
    
    @pytest.mark.asyncio
    async def test_analyze_task_request_is_async(self):
        """Test that analyze_task_request is an async coroutine."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                # Mock generate_content to return valid JSON
                mock_response = Mock()
                mock_response.text = '{"intent": "create_task", "summary": "Buy groceries", "due_date": "2025-11-21"}'
                mock_model.generate_content.return_value = mock_response
                
                llm_service = LLMService(api_key="test_key_123")
                current_date = datetime.now(MALAYSIA_TZ)
                
                # Mock asyncio.to_thread to execute synchronously in tests
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.return_value = mock_response
                    
                    # Call should be awaitable
                    result = await llm_service.analyze_task_request(
                        user_message="Buy groceries tomorrow",
                        current_date=current_date,
                        last_task_context=None
                    )
                    
                    # Verify result
                    assert isinstance(result, TaskIntent)
                    assert result.intent == "create_task"
                    assert result.summary == "Buy groceries"
                    assert result.due_date == "2025-11-21"
                    
                    # Verify asyncio.to_thread was called
                    mock_to_thread.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_blocking_call_wrapped_in_asyncio_to_thread(self):
        """Test that blocking generate_content is wrapped with asyncio.to_thread."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                mock_response = Mock()
                mock_response.text = '{"intent": "create_task", "summary": "Test task", "due_date": null}'
                mock_model.generate_content.return_value = mock_response
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.return_value = mock_response
                    
                    await llm_service.analyze_task_request(
                        user_message="Test message",
                        current_date=current_date
                    )
                    
                    # Verify to_thread was called with model.generate_content
                    mock_to_thread.assert_called_once()
                    call_args = mock_to_thread.call_args[0]
                    assert call_args[0] == mock_model.generate_content
    
    @pytest.mark.asyncio
    async def test_error_handling_returns_fallback_async(self):
        """Test that exceptions during LLM inference return fallback TaskIntent asynchronously."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                # Mock asyncio.to_thread to raise exception
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = Exception("Network error")
                    
                    result = await llm_service.analyze_task_request(
                        user_message="Buy milk",
                        current_date=current_date
                    )
                    
                    # Should return fallback intent
                    assert isinstance(result, TaskIntent)
                    assert result.intent == "create_task"
                    assert result.summary == "Buy milk"  # Truncated to 12 words
                    assert result.confidence == 0.5
                    assert "llm_error" in result.raw_response
    
    @pytest.mark.asyncio
    async def test_json_parse_error_returns_fallback_async(self):
        """Test that JSON parsing errors return fallback TaskIntent asynchronously."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                # Mock invalid JSON response
                mock_response = Mock()
                mock_response.text = 'Invalid JSON {not valid}'
                mock_model.generate_content.return_value = mock_response
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.return_value = mock_response
                    
                    result = await llm_service.analyze_task_request(
                        user_message="Call dentist",
                        current_date=current_date
                    )
                    
                    # Should return fallback intent
                    assert isinstance(result, TaskIntent)
                    assert result.intent == "create_task"
                    assert result.confidence == 0.5
                    assert "json_parse_error" in result.raw_response
    
    @pytest.mark.asyncio
    async def test_multiple_intent_types_async(self):
        """Test different intent types are handled correctly in async mode."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                test_cases = [
                    ('{"intent": "create_task", "summary": "Buy milk", "due_date": "2025-11-22"}', "create_task", "Buy milk"),
                    ('{"intent": "update_due_date", "summary": "", "due_date": "2025-11-25"}', "update_due_date", ""),
                    ('{"intent": "unknown", "summary": "", "due_date": null}', "unknown", ""),
                ]
                
                for json_response, expected_intent, expected_summary in test_cases:
                    mock_response = Mock()
                    mock_response.text = json_response
                    
                    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                        mock_to_thread.return_value = mock_response
                        
                        result = await llm_service.analyze_task_request(
                            user_message="Test",
                            current_date=current_date
                        )
                        
                        assert result.intent == expected_intent
                        assert result.summary == expected_summary


class TestConcurrentLLMRequests:
    """Integration tests for concurrent non-blocking LLM requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_llm_requests_do_not_block(self):
        """Test that multiple LLM requests can be processed concurrently without blocking."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                # Mock slow LLM response (simulate 2 second inference)
                async def slow_llm_response(*args, **kwargs):
                    await asyncio.sleep(0.1)  # Simulate processing time
                    mock_response = Mock()
                    mock_response.text = '{"intent": "create_task", "summary": "Task", "due_date": null}'
                    return mock_response
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = slow_llm_response
                    
                    # Start 3 concurrent LLM requests
                    start_time = asyncio.get_event_loop().time()
                    
                    tasks = [
                        llm_service.analyze_task_request("Task 1", current_date),
                        llm_service.analyze_task_request("Task 2", current_date),
                        llm_service.analyze_task_request("Task 3", current_date),
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    end_time = asyncio.get_event_loop().time()
                    elapsed = end_time - start_time
                    
                    # All 3 requests should complete
                    assert len(results) == 3
                    for result in results:
                        assert isinstance(result, TaskIntent)
                        assert result.intent == "create_task"
                    
                    # Should take ~0.1s (concurrent), not ~0.3s (sequential)
                    # Using 0.25s as upper bound to account for test overhead
                    assert elapsed < 0.25, f"Requests took {elapsed:.3f}s, expected < 0.25s (concurrent execution)"
    
    @pytest.mark.asyncio
    async def test_llm_request_does_not_block_other_coroutines(self):
        """Test that LLM request allows other coroutines to run concurrently."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                # Track execution order
                execution_order = []
                
                async def slow_llm_response(*args, **kwargs):
                    execution_order.append("llm_start")
                    await asyncio.sleep(0.1)
                    execution_order.append("llm_end")
                    mock_response = Mock()
                    mock_response.text = '{"intent": "create_task", "summary": "Task", "due_date": null}'
                    return mock_response
                
                async def other_coroutine():
                    execution_order.append("other_start")
                    await asyncio.sleep(0.05)
                    execution_order.append("other_end")
                    return "completed"
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = slow_llm_response
                    
                    # Start LLM request and another coroutine concurrently
                    llm_task = llm_service.analyze_task_request("Test", current_date)
                    other_task = other_coroutine()
                    
                    await asyncio.gather(llm_task, other_task)
                    
                    # Other coroutine should start and finish while LLM is processing
                    assert "llm_start" in execution_order
                    assert "other_start" in execution_order
                    assert "other_end" in execution_order
                    assert "llm_end" in execution_order
                    
                    # Other coroutine should complete before LLM finishes
                    other_end_idx = execution_order.index("other_end")
                    llm_end_idx = execution_order.index("llm_end")
                    assert other_end_idx < llm_end_idx, "Other coroutine should complete before LLM"


class TestAsyncErrorHandling:
    """Tests for async error handling in LLM service."""
    
    @pytest.mark.asyncio
    async def test_network_error_preserves_async_behavior(self):
        """Test that network errors during LLM inference are handled asynchronously."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = ConnectionError("Network unreachable")
                    
                    # Should not raise, should return fallback
                    result = await llm_service.analyze_task_request(
                        user_message="Test task",
                        current_date=current_date
                    )
                    
                    assert isinstance(result, TaskIntent)
                    assert result.confidence == 0.5
                    assert "llm_error" in result.raw_response
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_error_handling(self):
        """Test that API rate limit errors return fallback asynchronously."""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = Mock()
                mock_model_class.return_value = mock_model
                
                llm_service = LLMService(api_key="test_key")
                current_date = datetime.now(MALAYSIA_TZ)
                
                with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.side_effect = Exception("429 Too Many Requests")
                    
                    result = await llm_service.analyze_task_request(
                        user_message="Another task",
                        current_date=current_date
                    )
                    
                    assert isinstance(result, TaskIntent)
                    assert result.intent == "create_task"
                    assert result.confidence == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
