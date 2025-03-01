import logging
import json
import re
from datetime import datetime
import threading

class ResponseProcessor:
    """Processes structured responses from LLM."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # These will be imported and initialized in the process_response method
        # to avoid circular imports
        self.action_manager = None
        self.notification_manager = None
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, response_text, question):
        """
        Process a structured response from the LLM.
        
        Args:
            response_text (str): Raw response text from LLM
            question (str): Original user question
            
        Returns:
            dict: Processed results and actions taken
        """
        # Import here to avoid circular imports
        from core.action_manager import ActionManager
        from core.notification_manager import NotificationManager
        
        # Initialize components if not already done
        if self.action_manager is None:
            self.action_manager = ActionManager(self.config_manager)
        
        if self.notification_manager is None:
            self.notification_manager = NotificationManager(self.config_manager)
        
        try:
            # Try to parse as JSON
            structured_response = self._extract_json(response_text)
            
            # If parsing fails, treat as plain text for speech
            if not structured_response:
                return {
                    "speech": response_text,
                    "raw_response": response_text,
                    "structured": False,
                    "actions_performed": []
                }
            
            # Validate required fields
            if "speech" not in structured_response:
                structured_response["speech"] = "I've processed your request but don't have anything specific to say."
            
            # Execute actions based on the response
            actions_performed = self.action_manager.execute_actions(structured_response, question)
            
            # Add metadata to the result
            result = {
                **structured_response,
                "raw_response": response_text,
                "structured": True,
                "actions_performed": actions_performed
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            return {
                "speech": f"I encountered an error processing the response: {str(e)}",
                "raw_response": response_text,
                "structured": False,
                "actions_performed": []
            }
    
    def _extract_json(self, text):
        """
        Extract JSON from text, handling various formats.
        
        Args:
            text (str): Text that may contain JSON
            
        Returns:
            dict: Extracted JSON or None if not found/invalid
        """
        try:
            # First try direct JSON parsing in case the entire text is JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in code blocks
            json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, text)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            # Try to find JSON with curly braces if code blocks didn't work
            json_pattern = r'({[\s\S]*?})'
            matches = re.findall(json_pattern, text)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            # If we get here, no valid JSON was found
            self.logger.warning("No valid JSON structure found in response")
            return None 