import logging
from datetime import datetime
import threading

class ActionManager:
    """Manages execution of various actions from AI responses."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Import here to avoid circular imports
        from core.clipboard_util import ClipboardUtil
        from core.keyboard_automation import KeyboardAutomation
        from core.notes_manager import NotesManager
        from core.notification_manager import NotificationManager
        
        self.clipboard_util = ClipboardUtil()
        self.keyboard_automation = KeyboardAutomation()
        self.notes_manager = NotesManager(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        self.auto_execute = config_manager.get("actions", "auto_execute", False)
        self.logger = logging.getLogger(__name__)
    
    def execute_actions(self, parsed_response, original_question):
        """
        Execute the actions in the parsed response.
        
        Args:
            parsed_response (dict): Structured response with actions
            original_question (str): Original user question
            
        Returns:
            list: Actions that were performed
        """
        actions_performed = []
        
        # Handle clipboard content
        if "clipboard" in parsed_response and parsed_response["clipboard"]:
            content = parsed_response["clipboard"]
            if self.clipboard_util.copy_to_clipboard(content):
                actions_performed.append({"type": "clipboard", "content": content})
        
        # Handle notes
        if "notes" in parsed_response and parsed_response["notes"]:
            notes_data = parsed_response["notes"]
            if isinstance(notes_data, dict):
                title = notes_data.get("title", f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                content = notes_data.get("content", "")
                
                if content:
                    self.notes_manager.add_note(title, content, original_question)
                    actions_performed.append({"type": "notes", "title": title})
        
        # Handle macro execution
        if "macro" in parsed_response and parsed_response["macro"]:
            macro_data = parsed_response["macro"]
            
            if isinstance(macro_data, dict):
                keys = macro_data.get("keys", "")
                description = macro_data.get("description", "Execute keyboard shortcut")
                
                if keys:
                    # Check if we need confirmation
                    execute = self.auto_execute
                    
                    if not execute:
                        # Request confirmation
                        confirmation_message = f"Execute keyboard shortcut: {description} ({keys})"
                        execute = self.notification_manager.show_confirmation(confirmation_message)
                    
                    # Execute if confirmed or auto-execute is enabled
                    if execute:
                        if self.keyboard_automation.execute_sequence(keys):
                            actions_performed.append({
                                "type": "macro", 
                                "keys": keys, 
                                "description": description
                            })
        
        return actions_performed 