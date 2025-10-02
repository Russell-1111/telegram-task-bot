"""
Date formatting module for Outlook API integration.

This module handles:
- Validating date strings in YYYY-MM-DD format
- Processing dates relative to Malaysia timezone
- Converting dates to Outlook API format
- Handling invalid and past dates gracefully
"""

import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

# Malaysia timezone for consistent date handling
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def validate_and_process_date(date_string):
    """
    Validate and process a date string in YYYY-MM-DD format.
    
    Features:
    - Validates ISO date format (YYYY-MM-DD)
    - Uses Malaysia timezone for current date comparison
    - Rejects dates in the past (replaces with current date)
    - Handles null/empty inputs gracefully
    - Comprehensive logging for debugging
    
    Args:
        date_string (str): Date in YYYY-MM-DD format, "null", or None
    
    Returns:
        str: Validated date string in YYYY-MM-DD format, or None if invalid
             - Returns None for null/empty inputs
             - Returns current date (Malaysia time) for past dates
             - Returns original date for valid future dates
    
    Example:
        >>> validate_and_process_date("2025-12-31")
        '2025-12-31'
        >>> validate_and_process_date("2020-01-01")  # Past date
        '2024-12-15'  # Current date
        >>> validate_and_process_date("null")
        None
        >>> validate_and_process_date("invalid-date")
        None
    """
    if not date_string or date_string == "null":
        return None
    
    try:
        # Validate ISO date format (YYYY-MM-DD)
        parsed_date = datetime.fromisoformat(date_string).date()
        current_date_malaysia = datetime.now(MALAYSIA_TZ).date()
        
        # Check if date is not in the past (based on Malaysia timezone)
        if parsed_date >= current_date_malaysia:
            logger.info(f"Valid due date: {date_string}")
            return date_string
        else:
            logger.warning(f"Due date {date_string} is in the past (Malaysia time), using current date instead")
            return current_date_malaysia.isoformat()
    except (ValueError, TypeError) as date_error:
        logger.error(f"Invalid due date format '{date_string}': {date_error}")
        return None


def format_due_date_for_outlook(date_string):
    """
    Convert a YYYY-MM-DD date string to datetime format for Outlook API.
    
    Features:
    - Converts date to Microsoft Graph API format
    - Defaults to 5:00 PM (17:00) Malaysia time
    - Handles missing/invalid dates with current date fallback
    - Localizes to Malaysia timezone
    - Returns format expected by Microsoft Graph API
    
    Args:
        date_string (str): Date in YYYY-MM-DD format, or None
    
    Returns:
        str: Datetime string in Microsoft Graph API format
             Format: "YYYY-MM-DDTHH:MM:SS.0000000"
             Time: 17:00:00 (5:00 PM) Malaysia time
             Fallback: Current date at 5:00 PM if input is invalid
    
    Technical Details:
        - Microsoft Graph expects datetime without timezone suffix
        - Timezone is specified separately in the API request
        - Format uses 7 decimal places for fractional seconds (required by API)
        - Time component set to 17:00 (5:00 PM) as sensible task due time
    
    Example:
        >>> format_due_date_for_outlook("2024-12-31")
        '2024-12-31T17:00:00.0000000'
        >>> format_due_date_for_outlook(None)
        '2024-12-15T17:00:00.0000000'  # Current date at 5 PM
        >>> format_due_date_for_outlook("invalid")
        '2024-12-15T17:00:00.0000000'  # Fallback to current date
    """
    if not date_string:
        # Fallback to current date in Malaysia timezone
        malaysia_now = datetime.now(MALAYSIA_TZ).replace(hour=17, minute=0, second=0, microsecond=0)
        # Microsoft Graph expects datetime without timezone info (timezone specified separately)
        return malaysia_now.strftime("%Y-%m-%dT%H:%M:%S.0000000")
    
    try:
        # Parse the date and set time to 5:00 PM Malaysia time
        date_obj = datetime.fromisoformat(date_string).replace(hour=17, minute=0, second=0, microsecond=0)
        # Localize to Malaysia timezone 
        malaysia_datetime = MALAYSIA_TZ.localize(date_obj)
        # Microsoft Graph expects datetime in local timezone format without timezone suffix
        return malaysia_datetime.strftime("%Y-%m-%dT%H:%M:%S.0000000")
    except (ValueError, TypeError):
        # Fallback to current date/time in Malaysia timezone if parsing fails
        malaysia_now = datetime.now(MALAYSIA_TZ).replace(hour=17, minute=0, second=0, microsecond=0)
        return malaysia_now.strftime("%Y-%m-%dT%H:%M:%S.0000000")
