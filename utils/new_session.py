import os
import sys
import datetime

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from config.config_manager import ConfigManager
from core.session_manager import SessionManager

def create_new_session():
    """Create a new session file and print its path."""
    try:
        # Initialize config and session manager
        config_manager = ConfigManager()
        session_manager = SessionManager(config_manager)
        
        # Create a new session
        new_session_path = session_manager.create_new_session()
        
        print(f"Created new session: {new_session_path}")
        print(f"Next time you start the application, it will use this session.")
        
        # Update config to use the new session (in a full implementation)
        # In this prototype, we'd need to modify the config file directly
        
    except Exception as e:
        print(f"Error creating new session: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(create_new_session())