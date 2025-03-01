import logging
import os
import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionManager:
    """Handles conversation session management, reading and writing to markdown files."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.sessions_dir = config_manager.get("session", "sessions_directory", "sessions")
        self.current_session_file = self._get_session_file()
        
        # Ensure session directory exists
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def _get_session_file(self):
        """
        Determine the session file to use based on configuration.
        
        Returns:
            str: Path to the session file
        """
        # Check if we need to create a new session
        if self.config_manager.get_new_session_on_startup():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.md"
            return os.path.join(self.sessions_dir, filename)
        
        # Otherwise use the default session file
        return self.config_manager.get_session_file()
    
    def create_new_session(self):
        """
        Create a new session file.
        
        Returns:
            str: Path to the new session file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.md"
        new_session_path = os.path.join(self.sessions_dir, filename)
        
        self.current_session_file = new_session_path
        logger.info(f"Created new session: {new_session_path}")
        
        return new_session_path
    
    def get_conversation_history(self, max_entries=5):
        """
        Get the recent conversation history from the current session file.
        
        Args:
            max_entries (int): Maximum number of conversation entries to include
            
        Returns:
            str: Recent conversation history as a formatted string
        """
        if not os.path.exists(self.current_session_file):
            return ""
        
        try:
            with open(self.current_session_file, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # In a real implementation, you'd parse the markdown more carefully
            # For the prototype, we'll just return the whole file if it's not too large
            return content
            
        except Exception as e:
            logger.error(f"Error reading conversation history: {e}")
            return ""
    
    def add_interaction(self, question, answer):
        """
        Add a new interaction to the session file.
        
        Args:
            question (str): User's question
            answer (str): AI's answer
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the current timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format the interaction as markdown
            interaction = f"\n\n## Question ({timestamp})\n\n{question}\n\n## Answer\n\n{answer}"
            
            # Create a new file if it doesn't exist
            if not os.path.exists(self.current_session_file):
                with open(self.current_session_file, 'w', encoding='utf-8') as file:
                    file.write(f"# AI Assistant Session\n\nStarted: {timestamp}")
            
            # Append the new interaction
            with open(self.current_session_file, 'a', encoding='utf-8') as file:
                file.write(interaction)
            
            logger.info(f"Added new interaction to session file: {self.current_session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding interaction to session file: {e}")
            return False