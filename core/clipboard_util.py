import logging

class ClipboardUtil:
    """Utility for copying content to the clipboard."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def copy_to_clipboard(self, text):
        """
        Copy text to system clipboard.
        
        Args:
            text (str): Text to copy to clipboard
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import pyperclip
            pyperclip.copy(text)
            self.logger.info(f"Copied to clipboard: {text[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"Error copying to clipboard: {e}")
            return False 