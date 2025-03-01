import logging
import threading
from pynput import keyboard
import time

logger = logging.getLogger(__name__)

class InputManager:
    """Handles keyboard input and shortcut detection."""
    
    def __init__(self, config_manager, on_press=None, on_release=None):
        self.config_manager = config_manager
        self.shortcut_key_str = config_manager.get_shortcut_key()
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        
        # Parse the shortcut key string (e.g., "ctrl+alt+a")
        self.shortcut_keys = self._parse_shortcut_key(self.shortcut_key_str)
        self.pressed_keys = set()
        self.listener = None
        self.is_shortcut_active = False
        
        logger.info(f"Configured shortcut key: {self.shortcut_key_str}")
    
    def _parse_shortcut_key(self, shortcut_str):
        """
        Parse the shortcut key string into components.
        
        Args:
            shortcut_str (str): Shortcut key string (e.g., "ctrl+alt+a")
            
        Returns:
            list: List of key components
        """
        return shortcut_str.lower().split('+')
    
    def _key_to_string(self, key):
        """
        Convert a pynput Key object to a string representation.
        
        Args:
            key: pynput Key object
            
        Returns:
            str: String representation of the key
        """
        try:
            # Handle special keys
            if hasattr(key, 'name'):
                return key.name.lower()
            
            # Handle normal character keys
            return key.char.lower()
        except AttributeError:
            # If we can't get a name or char, use the string representation
            return str(key).lower().replace("'", "")
    
    def on_key_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: pynput Key object
        """
        try:
            key_str = self._key_to_string(key)
            
            # Add to pressed keys set
            self.pressed_keys.add(key_str)
            
            # Check if all shortcut keys are pressed
            shortcut_activated = all(k in self.pressed_keys for k in self.shortcut_keys)
            
            # Only trigger the callback once when shortcut is first activated
            if shortcut_activated and not self.is_shortcut_active:
                self.is_shortcut_active = True
                logger.info("Shortcut key combination pressed")
                
                if self.on_press_callback:
                    self.on_press_callback()
            
        except Exception as e:
            logger.error(f"Error in key press handler: {e}")
    
    def on_key_release(self, key):
        """
        Handle key release events.
        
        Args:
            key: pynput Key object
        """
        try:
            key_str = self._key_to_string(key)
            
            # Remove from pressed keys set if present
            if key_str in self.pressed_keys:
                self.pressed_keys.remove(key_str)
            
            # Check if any shortcut key was released
            if self.is_shortcut_active and key_str in self.shortcut_keys:
                self.is_shortcut_active = False
                logger.info("Shortcut key combination released")
                
                if self.on_release_callback:
                    self.on_release_callback()
            
        except Exception as e:
            logger.error(f"Error in key release handler: {e}")
    
    def start_listening(self):
        """Start listening for keyboard events."""
        if self.listener:
            return
        
        try:
            # Create keyboard listener
            self.listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            
            # Start listener in a separate thread
            self.listener.start()
            logger.info("Keyboard listener started")
            
        except Exception as e:
            logger.error(f"Error starting keyboard listener: {e}")
    
    def stop_listening(self):
        """Stop listening for keyboard events."""
        if not self.listener:
            return
        
        try:
            self.listener.stop()
            self.listener = None
            logger.info("Keyboard listener stopped")
            
        except Exception as e:
            logger.error(f"Error stopping keyboard listener: {e}")