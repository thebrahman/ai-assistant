import os
import yaml
import logging
from pathlib import Path

class ConfigManager:
    """Handles loading and accessing configuration settings."""
    
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self._ensure_directories()
        
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def _setup_logging(self):
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
        log_file = self.config.get('logging', {}).get('file', 'ai_assistant.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
    def _ensure_directories(self):
        """Ensure required directories exist."""
        sessions_dir = self.config.get('session', {}).get('sessions_directory', 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)
    
    def get(self, section, key=None, default=None):
        """Get a configuration value."""
        if key is None:
            return self.config.get(section, default)
        
        return self.config.get(section, {}).get(key, default)
    
    def get_shortcut_key(self):
        """Get the keyboard shortcut configuration."""
        return self.config.get('keyboard', {}).get('shortcut_key', 'ctrl+alt+a')
    
    def get_session_file(self):
        """Get the current session file path."""
        sessions_dir = self.config.get('session', {}).get('sessions_directory', 'sessions')
        default_file = self.config.get('session', {}).get('default_session_file', 'ai_assistant_session.md')
        return os.path.join(sessions_dir, default_file)
    
    def get_new_session_on_startup(self):
        """Check if a new session should be created on startup."""
        return self.config.get('session', {}).get('new_session_on_startup', False)
    
    def get_gemini_api_key(self):
        """Get the Gemini API key."""
        return self.config.get('ai', {}).get('api_key', '')
