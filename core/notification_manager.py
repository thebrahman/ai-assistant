import logging
import threading
import sys

class NotificationManager:
    """Handles displaying notifications and getting user confirmation."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.timeout = config_manager.get("actions", "confirmation_timeout", 10)
        self.logger = logging.getLogger(__name__)
    
    def show_confirmation(self, action_description):
        """
        Show confirmation dialog and wait for user input.
        
        Args:
            action_description (str): Description of the action
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        print("\n" + "="*50)
        print(f"CONFIRMATION REQUIRED: {action_description}")
        print(f"Press Y to execute or N to cancel (timeout in {self.timeout} seconds)")
        print("="*50)
        
        # Use a separate thread to handle timeout
        result = {"confirmed": False}
        
        def get_input():
            try:
                while True:
                    user_input = input().strip().lower()
                    if user_input == 'y':
                        result["confirmed"] = True
                        return
                    elif user_input == 'n':
                        result["confirmed"] = False
                        return
                    else:
                        print("Invalid input. Press Y to execute or N to cancel.")
            except Exception as e:
                self.logger.error(f"Error getting confirmation input: {e}")
                result["confirmed"] = False
        
        # Start input thread
        input_thread = threading.Thread(target=get_input)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait for input or timeout
        input_thread.join(timeout=self.timeout)
        
        if input_thread.is_alive():
            # Timeout occurred
            print("Confirmation timeout - action cancelled")
            return False
        
        return result["confirmed"]
    
    def show_notification(self, message):
        """
        Show a simple notification message to the user.
        
        Args:
            message (str): Message to display
        """
        print("\n" + "-"*50)
        print(message)
        print("-"*50) 