"""
LLM Service for Task Intent Detection

This service handles all interactions with Google's Gemini AI for:
- Analyzing user messages to detect intent
- Extracting task summaries
- Parsing due dates
- JSON response processing

This abstraction allows easy swapping of LLM providers (Gemini → OpenAI, etc.)
"""
import google.generativeai as genai
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskIntent:
    """
    Structured representation of LLM-analyzed task intent
    
    Attributes:
        intent: Type of action ('create_task', 'update_due_date', 'unknown')
        summary: Task summary (3-12 words for create_task, empty for others)
        due_date: Due date in YYYY-MM-DD format or None
        confidence: Confidence score (0.0-1.0), default 1.0
        raw_response: Original LLM response for debugging
    """
    intent: str
    summary: str
    due_date: Optional[str]
    confidence: float = 1.0
    raw_response: str = ""


class LLMService:
    """
    Handles all LLM interactions for task intent detection.
    
    This service encapsulates Gemini AI integration and provides a clean
    interface for analyzing user messages. Can be easily swapped for other
    LLM providers by implementing the same interface.
    
    Example:
        llm = LLMService(api_key=config.gemini_api_key)
        
        intent = llm.analyze_task_request(
            user_message="Buy groceries tomorrow",
            current_date=datetime.now(),
            last_task_context={'title': 'Previous task', 'due_date': '2025-10-01'}
        )
        
        if intent.intent == 'create_task':
            create_task(intent.summary, intent.due_date)
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the LLM Service
        
        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.5-flash)
        """
        if not api_key:
            raise ValueError("API key is required for LLM Service")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        logger.info(f"LLM Service initialized with model: {model_name}")
    
    def analyze_task_request(
        self,
        user_message: str,
        current_date: datetime,
        last_task_context: Optional[Dict[str, Any]] = None
    ) -> TaskIntent:
        """
        Analyze user message and extract task intent.
        
        Args:
            user_message: The user's input message
            current_date: Current date/time in the appropriate timezone
            last_task_context: Optional context about user's last task
                              {'title': str, 'due_date': str or None}
        
        Returns:
            TaskIntent with parsed information
            
        Raises:
            Exception: If LLM analysis fails completely
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(user_message, current_date, last_task_context)
            
            # Call LLM
            logger.debug(f"Sending request to {self.model_name} for message: '{user_message}'")
            response = self.model.generate_content(prompt)
            raw_response = response.text
            
            # Parse response
            intent = self._parse_response(raw_response)
            intent.raw_response = raw_response
            
            logger.info(
                f"LLM Analysis - Intent: {intent.intent}, "
                f"Summary: '{intent.summary}', Due: {intent.due_date}"
            )
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            # Return safe fallback
            return self._create_fallback_intent(user_message, "json_parse_error")
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Return safe fallback
            return self._create_fallback_intent(user_message, "llm_error")
    
    def _build_prompt(
        self,
        message: str,
        current_date: datetime,
        last_task: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Build structured prompt for Gemini.
        
        This method creates a comprehensive prompt with:
        - Context (current date, timezone, last task)
        - Intent detection rules
        - Summary generation rules
        - Due date extraction rules
        - Examples
        
        Args:
            message: User's message
            current_date: Current date in appropriate timezone
            last_task: Optional last task context
        
        Returns:
            List of prompt parts for Gemini
        """
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")
        
        # Build context
        context = f"Today is {date_str} ({weekday}) in Malaysia timezone (UTC+8)"
        if last_task:
            task_title = last_task.get('title', 'Unknown')
            task_due = last_task.get('due_date', 'no date set')
            context += f". User's last created task: '{task_title}' (due: {task_due})"
        
        prompt_parts = [
            "You are an intelligent task assistant. Your job is to analyze user requests and identify if they want to:",
            "1. Create a new task",
            "2. Update the due date of their last created task",
            "3. Something else (unknown intent)",
            f"Context: {context}.",
            "Always respond with a JSON object with three keys: 'intent', 'summary', and 'due_date'.",
            "",
            "Intent Detection Rules:",
            "- Set 'intent' to 'create_task' if the user wants to create/add/remember a NEW task",
            "- Set 'intent' to 'update_due_date' if the user wants to change/update/modify the due date of their existing task",
            "- Set 'intent' to 'unknown' for other requests",
            "",
            "Summary Rules:",
            "- For new tasks: CONDENSE the user's message into a clear, action-focused summary (3-12 words)",
            "- REMOVE filler phrases: 'I want to', 'I need to', 'I have to', 'I would like to', 'Can you', 'Please'",
            "- EXTRACT the core action and object: focus on what needs to be done, not how the user phrased it",
            "- Use strong action verbs at the start: Draft, Create, Submit, Review, Complete, etc.",
            "- Examples of transformation:",
            "  • 'I want to have a draft for my literature review using llm' -> 'Draft literature review using LLM'",
            "  • 'I need to buy groceries and milk tomorrow' -> 'Buy groceries and milk'",
            "  • 'Can you remind me to call the dentist?' -> 'Call dentist'",
            "  • 'Please help me submit my report by Friday' -> 'Submit report'",
            "- For due date updates: use empty string (the existing task title will be used)",
            "- For unknown: use empty string",
            "",
            "Due Date Extraction Rules:",
            "- Extract explicit dates: 'October 26th' -> '2025-10-26', 'Dec 15' -> '2025-12-15'",
            "- Handle relative dates: 'tomorrow' -> next day, 'next Friday' -> next occurring Friday",
            "- Process time expressions: 'in 3 days' -> 3 days from today, 'next week' -> 7 days from today",
            "- Handle ambiguous dates: 'Friday' (if today is Wednesday) -> this Friday",
            "- Set 'due_date' to YYYY-MM-DD format or null if no date found",
            "- If user says 'today', use today's date. If 'tonight' or 'this evening', also use today's date",
            "- All dates should be calculated based on Malaysia timezone",
            "",
            "Examples:",
            "User: 'Buy groceries tomorrow' -> {'intent': 'create_task', 'summary': 'Buy groceries', 'due_date': '2025-10-07'}",
            "User: 'I want to have a draft for my literature review using llm' -> {'intent': 'create_task', 'summary': 'Draft literature review using LLM', 'due_date': null}",
            "User: 'I need to call the dentist on Friday' -> {'intent': 'create_task', 'summary': 'Call dentist', 'due_date': '2025-10-10'}",
            "User: 'Submit report by December 1st' -> {'intent': 'create_task', 'summary': 'Submit report', 'due_date': '2025-12-01'}",
            "User: 'Change due date to Friday' -> {'intent': 'update_due_date', 'summary': '', 'due_date': '2025-10-10'}",
            "User: 'What time is it?' -> {'intent': 'unknown', 'summary': '', 'due_date': null}",
            "User: 'Hello!' -> {'intent': 'unknown', 'summary': '', 'due_date': null}",
            "User: 'How are you doing?' -> {'intent': 'unknown', 'summary': '', 'due_date': null}",
            "User: 'Thanks' -> {'intent': 'unknown', 'summary': '', 'due_date': null}",
            "",
            f"Now analyze this request and provide your JSON response:\nUser Request: '{message}'"
        ]
        
        return prompt_parts
    
    def _parse_response(self, response_text: str) -> TaskIntent:
        """
        Extract JSON from LLM response and create TaskIntent.
        
        Handles various response formats:
        - ```json {...} ```
        - ``` {...} ```
        - Plain JSON {...}
        
        Args:
            response_text: Raw LLM response
        
        Returns:
            TaskIntent with parsed data
            
        Raises:
            json.JSONDecodeError: If JSON parsing fails
        """
        # Extract JSON from potential markdown formatting
        cleaned = self._extract_json_from_markdown(response_text)
        
        try:
            data = json.loads(cleaned)
            
            return TaskIntent(
                intent=data.get("intent", "unknown"),
                summary=data.get("summary", ""),
                due_date=data.get("due_date"),
                confidence=1.0
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {response_text}")
            raise
    
    def _extract_json_from_markdown(self, response_text: str) -> str:
        """
        Extract JSON from response that may be wrapped in markdown code blocks.
        
        Args:
            response_text: Raw response that may contain markdown
        
        Returns:
            Cleaned JSON string
        """
        response_text = response_text.strip()
        
        # Handle ```json ... ``` format
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # Handle ``` ... ``` format
        elif response_text.startswith("```") and response_text.count("```") >= 2:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                return response_text[start:end].strip()
        
        # Handle plain JSON (no markdown)
        elif response_text.startswith("{") and response_text.endswith("}"):
            return response_text
        
        # Try to find JSON object in the text
        else:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                return response_text[start:end]
        
        return response_text
    
    def _create_fallback_intent(self, user_message: str, reason: str) -> TaskIntent:
        """
        Create a safe fallback intent when LLM analysis fails.
        
        Args:
            user_message: Original user message
            reason: Reason for fallback
        
        Returns:
            TaskIntent with 'create_task' intent and truncated message
        """
        logger.warning(f"Creating fallback intent due to: {reason}")
        
        # Truncate message to reasonable length (max 12 words)
        truncated_summary = ' '.join(user_message.split()[:12])
        
        return TaskIntent(
            intent='create_task',
            summary=truncated_summary,
            due_date=None,
            confidence=0.5,
            raw_response=f"Fallback due to: {reason}"
        )
