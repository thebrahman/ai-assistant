import os
import json
import logging
import uuid
from datetime import datetime

class NotesManager:
    """Manages note-taking functionality."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Get application root directory (where app.py is located)
        self.app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Get notes file path from config, with default as "notes/notes.json"
        notes_path = config_manager.get("actions", "notes_file", "notes/notes.json")
        
        # Ensure notes_path is not None
        if notes_path is None:
            notes_path = "notes/notes.json"
            print(f"WARNING: notes_file configuration is None, using default: {notes_path}")
        
        # If path is not absolute, make it absolute relative to app root
        if not os.path.isabs(notes_path):
            self.notes_file = os.path.join(self.app_root, notes_path)
        else:
            self.notes_file = notes_path
            
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Notes file configured at: {self.notes_file}")
        self._ensure_notes_file()
    
    def _ensure_notes_file(self):
        """Ensure the notes file exists with valid JSON structure."""
        try:
            # Create directory if it doesn't exist
            notes_dir = os.path.dirname(self.notes_file)
            if not os.path.exists(notes_dir):
                os.makedirs(notes_dir, exist_ok=True)
                self.logger.info(f"Created notes directory: {notes_dir}")
            
            # Create file if it doesn't exist
            if not os.path.exists(self.notes_file):
                with open(self.notes_file, 'w', encoding='utf-8') as f:
                    json.dump({"notes": []}, f, indent=2)
                self.logger.info(f"Created new notes file: {self.notes_file}")
        except Exception as e:
            self.logger.error(f"Failed to create notes file at {self.notes_file}: {e}")
            # Print to stdout as well for debugging
            print(f"ERROR: Failed to create notes file at {self.notes_file}: {e}")
    
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
            # Ensure file exists before trying to read it
            self._ensure_notes_file()
            
            # Create note object
            note = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "created_at": datetime.now().isoformat(),
                "related_question": related_question
            }
            
            # Read existing notes
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # If file doesn't exist or is invalid, create a new data structure
                self.logger.warning(f"Notes file missing or corrupted ({str(e)}). Creating new one.")
                data = {"notes": []}
            
            # Add new note
            if "notes" not in data:
                data["notes"] = []
            
            data["notes"].append(note)
            
            # Write back
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Added note: '{title}' to {self.notes_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding note '{title}': {e}")
            # Print to stdout as well for debugging
            print(f"ERROR: Failed to add note '{title}' to {self.notes_file}: {e}")
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
            # Ensure file exists before trying to read it
            self._ensure_notes_file()
            
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Return most recent notes
            notes = data.get("notes", [])
            return notes[-limit:] if limit > 0 else notes
            
        except Exception as e:
            self.logger.error(f"Error getting notes: {e}")
            return [] 