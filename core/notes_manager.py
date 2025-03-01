import os
import json
import logging
import uuid
from datetime import datetime

class NotesManager:
    """Manages note-taking functionality."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.notes_file = config_manager.get("actions", "notes_file", "notes.json")
        self.logger = logging.getLogger(__name__)
        self._ensure_notes_file()
    
    def _ensure_notes_file(self):
        """Ensure the notes file exists with valid JSON structure."""
        if not os.path.exists(self.notes_file):
            os.makedirs(os.path.dirname(os.path.abspath(self.notes_file)), exist_ok=True)
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump({"notes": []}, f, indent=2)
    
    def add_note(self, title, content, related_question=None):
        """
        Add a note to the notes file.
        
        Args:
            title (str): Note title
            content (str): Note content
            related_question (str, optional): The question that generated this note
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create note object
            note = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "related_question": related_question
            }
            
            # Read existing notes
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add new note
            if "notes" not in data:
                data["notes"] = []
            
            data["notes"].append(note)
            
            # Write back
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Added note: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding note: {e}")
            return False
    
    def get_notes(self, limit=10):
        """
        Get recent notes.
        
        Args:
            limit (int): Maximum number of notes to return (most recent)
            
        Returns:
            list: List of note objects
        """
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Return most recent notes
            notes = data.get("notes", [])
            return notes[-limit:] if limit > 0 else notes
            
        except Exception as e:
            self.logger.error(f"Error getting notes: {e}")
            return [] 