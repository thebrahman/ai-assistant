import logging
import json
import re
from datetime import datetime
import threading
import os
import pyperclip
import subprocess

logger = logging.getLogger(__name__)

# Use the same llm_logger from gemini_connector
llm_logger = logging.getLogger("llm_responses")

class ResponseProcessor:
    """Processes AI responses and executes actions."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize action manager and notification manager
        from core.action_manager import ActionManager
        from core.notification_manager import NotificationManager
        self.action_manager = ActionManager(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        
        # Load plugin settings
        self.plugins_enabled = config_manager.get("plugins", "enabled", default=False)
        self.plugins_dir = config_manager.get("plugins", "directory", default="plugins")
        
        # Load template settings
        self.templates_dir = config_manager.get("templates", "directory", default="templates")
        
        # LLM response logging configuration
        self.log_llm_responses = config_manager.get("logging", "log_llm_responses", default=True)
        
        # Ensure directories exist
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def process_response(self, raw_response, query):
        """
        Process the raw AI response and extract structured data.
        
        Args:
            raw_response (str): The raw response from the AI model
            query (str): The original user query
            
        Returns:
            dict: Processed response with action results
        """
        try:
            # Initialize basic response structure
            processed = {
                "speech": raw_response,
                "raw_response": raw_response,
                "structured": False,
                "actions_performed": []
            }
            
            # Extract JSON content if available
            json_data = self._extract_json(raw_response)
            
            # Log the JSON extraction result
            if self.log_llm_responses:
                self._log_response_processing(query, raw_response, json_data)
            
            if not json_data:
                # Handle unstructured response
                self.logger.info("Response is not structured JSON, returning raw text")
                return processed
            
            # Update with structured data
            processed.update(json_data)
            processed["structured"] = True
            
            # Process actions using the action manager
            if self.action_manager:
                actions_performed = self.action_manager.execute_actions(json_data, query)
                processed["actions_performed"] = actions_performed
                self.logger.info(f"Actions performed: {actions_performed}")
            else:
                self.logger.error("Action manager not initialized, skipping action execution")
            
            # Process clipboard action directly (for backward compatibility)
            if "clipboard" in json_data and json_data["clipboard"] and not any(a.get("type") == "clipboard" for a in processed["actions_performed"]):
                success = self._copy_to_clipboard(json_data["clipboard"])
                processed["actions_performed"].append({
                    "action": "clipboard",
                    "success": success
                })
            
            # Process macro action directly (for backward compatibility)
            if "macro" in json_data and json_data["macro"] and not any(a.get("type") == "macro" for a in processed["actions_performed"]):
                # Log the macro structure before attempting to process it
                if self.log_llm_responses:
                    self._log_macro_processing(json_data["macro"])
                
                result = self._run_macro(json_data["macro"])
                processed["actions_performed"].append({
                    "action": "macro",
                    "result": result
                })
            
            # Use the "speech" field for TTS if available
            if "speech" in json_data and json_data["speech"]:
                processed["speech"] = json_data["speech"]
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            
            # Log the error in processing
            if self.log_llm_responses:
                self._log_processing_error(query, raw_response, str(e))
            
            return {
                "speech": f"I encountered an error processing the response: {str(e) if hasattr(e, '__str__') else 'Unknown error'}",
                "raw_response": raw_response,
                "structured": False,
                "actions_performed": []
            }
    
    def _extract_json(self, text):
        """
        Extract JSON content from text.
        
        Args:
            text (str): Text potentially containing JSON
            
        Returns:
            dict: Extracted JSON data or None if not found
        """
        if not text:
            return None
            
        # Look for JSON-like content enclosed in ``` blocks (markdown code blocks)
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, text)
        
        for json_str in matches:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.logger.warning("Found JSON-like content but couldn't parse it")
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            self.logger.info("Response does not contain valid JSON")
            return None
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            pyperclip.copy(text)
            self.logger.info(f"Copied to clipboard: {text[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            return False
    
    def _run_macro(self, macro_command):
        """
        Run a macro command.
        
        Args:
            macro_command (dict or str): The macro command to execute - can be a string or
                a dict with 'description' and 'keys' fields
            
        Returns:
            str: Result of the macro execution
        """
        # For security, we'll restrict macro execution to a allowlist
        # This is a simplified implementation
        try:
            # Check if macros are enabled
            macros_enabled = self.config_manager.get("macros", "enabled", default=False)
            if not macros_enabled:
                self.logger.warning("Macro execution attempted but macros are disabled")
                return "Macros are disabled in configuration"
            
            # Handle different formats of the macro_command
            macro_keys = None
            macro_description = "Unknown macro"
            
            # If it's a dictionary with 'keys' field
            if isinstance(macro_command, dict):
                if 'keys' in macro_command:
                    macro_keys = macro_command['keys']
                    if 'description' in macro_command:
                        macro_description = macro_command['description']
                    self.logger.info(f"Executing macro: {macro_description} with keys: {macro_keys}")
                else:
                    self.logger.warning(f"Macro dict has no 'keys' field: {macro_command}")
                    return "Invalid macro format: no keys specified"
            # If it's a string, use it directly as keys
            elif isinstance(macro_command, str):
                macro_keys = macro_command
                self.logger.info(f"Executing macro with keys: {macro_keys}")
            else:
                self.logger.warning(f"Unsupported macro type: {type(macro_command)}")
                return f"Unsupported macro type: {type(macro_command).__name__}"
            
            # In a real implementation, you would have a secure way to execute commands
            # For now, just log what would be executed
            return f"Simulated macro execution: {macro_keys}"
            
        except Exception as e:
            self.logger.error(f"Error executing macro: {e}")
            return f"Error executing macro: {str(e)}"
    
    def _log_response_processing(self, query, raw_response, json_data):
        """
        Log the response processing details.
        
        Args:
            query (str): The original user query
            raw_response (str): The raw response from the LLM
            json_data (dict): The extracted JSON data (or None if extraction failed)
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "phase": "processing",
                "query": query,
                "json_extraction_success": json_data is not None,
                "extracted_structure": json_data if json_data else None
            }
            
            # Log as a single JSON line for easy parsing
            llm_logger.info(json.dumps(log_entry, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Error logging response processing: {e}")
    
    def _log_macro_processing(self, macro_data):
        """
        Log details about the macro structure before processing.
        
        Args:
            macro_data: The macro data from the JSON response
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "phase": "macro_processing",
                "macro_type": type(macro_data).__name__,
                "macro_content": macro_data
            }
            
            # Log as a single JSON line for easy parsing
            llm_logger.info(json.dumps(log_entry, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Error logging macro processing: {e}")
    
    def _log_processing_error(self, query, raw_response, error_msg):
        """
        Log errors that occur during response processing.
        
        Args:
            query (str): The original user query
            raw_response (str): The raw response from the LLM
            error_msg (str): The error message
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "phase": "processing_error",
                "query": query,
                "error": error_msg
            }
            
            # Log as a single JSON line for easy parsing
            llm_logger.info(json.dumps(log_entry, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Error logging processing error: {e}") 