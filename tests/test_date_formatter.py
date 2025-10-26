"""
Unit tests for date_formatter module

Tests cover:
- Date validation and processing
- Outlook API date formatting
- Timezone handling
- Edge cases (past dates, null values, invalid formats)
"""
import pytest
from datetime import datetime, timedelta
import pytz
from formatters.date_formatter import validate_and_process_date, format_due_date_for_outlook


MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


class TestDateFormatter:
    """Test suite for date formatter functions"""
    
    def test_validate_and_process_date_valid_future(self):
        """Test validating a valid future date"""
        future_date = (datetime.now(MALAYSIA_TZ) + timedelta(days=5)).date().isoformat()
        result = validate_and_process_date(future_date)
        
        assert result == future_date
    
    def test_validate_and_process_date_null(self):
        """Test validating null date"""
        result = validate_and_process_date("null")
        assert result is None
        
        result = validate_and_process_date(None)
        assert result is None
    
    def test_validate_and_process_date_empty(self):
        """Test validating empty date"""
        result = validate_and_process_date("")
        assert result is None
    
    def test_validate_and_process_date_past(self):
        """Test validating a past date - should return current date"""
        past_date = (datetime.now(MALAYSIA_TZ) - timedelta(days=5)).date().isoformat()
        result = validate_and_process_date(past_date)
        
        current_date = datetime.now(MALAYSIA_TZ).date().isoformat()
        assert result == current_date
    
    def test_validate_and_process_date_today(self):
        """Test validating today's date"""
        today = datetime.now(MALAYSIA_TZ).date().isoformat()
        result = validate_and_process_date(today)
        
        assert result == today
    
    def test_validate_and_process_date_invalid_format(self):
        """Test validating invalid date format"""
        result = validate_and_process_date("invalid-date")
        assert result is None
        
        result = validate_and_process_date("2025-13-01")  # Invalid month
        assert result is None
        
        result = validate_and_process_date("not a date")
        assert result is None
    
    def test_format_due_date_for_outlook_valid(self):
        """Test formatting a valid date for Outlook API"""
        date_str = "2025-12-31"
        result = format_due_date_for_outlook(date_str)
        
        # Should be in format: YYYY-MM-DDTHH:MM:SS.0000000
        assert result == "2025-12-31T17:00:00.0000000"
    
    def test_format_due_date_for_outlook_none(self):
        """Test formatting None date - should return current date"""
        result = format_due_date_for_outlook(None)
        
        # Should still return a valid format
        assert "T17:00:00.0000000" in result
        assert len(result) == 27  # YYYY-MM-DDTHH:MM:SS.0000000
    
    def test_format_due_date_for_outlook_empty(self):
        """Test formatting empty date"""
        result = format_due_date_for_outlook("")
        
        # Should fallback to current date
        assert "T17:00:00.0000000" in result
    
    def test_format_due_date_for_outlook_invalid(self):
        """Test formatting invalid date - should fallback gracefully"""
        result = format_due_date_for_outlook("invalid-date")
        
        # Should still return a valid format (current date fallback)
        assert "T17:00:00.0000000" in result
    
    def test_format_due_date_for_outlook_time_component(self):
        """Test that formatted date always uses 5 PM (17:00)"""
        date_str = "2025-06-15"
        result = format_due_date_for_outlook(date_str)
        
        assert "T17:00:00" in result
    
    def test_format_due_date_for_outlook_correct_format(self):
        """Test that output format matches Microsoft Graph API requirements"""
        date_str = "2025-10-28"
        result = format_due_date_for_outlook(date_str)
        
        # Format should be: YYYY-MM-DDTHH:MM:SS.0000000 (exactly 27 characters)
        assert len(result) == 27
        assert result[10] == 'T'
        assert result[19] == '.'
        assert result.endswith('0000000')
    
    def test_timezone_awareness(self):
        """Test that dates are processed in Malaysia timezone"""
        # Create a date that's today in Malaysia but might be yesterday elsewhere
        malaysia_now = datetime.now(MALAYSIA_TZ)
        today_malaysia = malaysia_now.date().isoformat()
        
        result = validate_and_process_date(today_malaysia)
        assert result == today_malaysia  # Should be valid (not past) in Malaysia TZ
