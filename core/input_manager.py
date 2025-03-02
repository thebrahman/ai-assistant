import logging
import threading
from pynput import keyboard
import time

logger = logging.getLogger(__name__)

class InputManager:
    """Handles keyboard input and shortcut detection."""
    
    def __init__(self, config_manager, on_press=None, on_release=None):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Get shortcut key from config
        self.shortcut_key = config_manager.get_shortcut_key()
        self.logger.info(f"Configured shortcut key: {self.shortcut_key}")
        
        # Set up callbacks
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        
        # Parse shortcut key
        self.keys = self._parse_shortcut_key(self.shortcut_key)
        self.currently_pressed = set()
        
        # Flag to track if shortcut is already active
        self.shortcut_active = False
        
        # Flag to temporarily suppress key events during TTS and other operations
        # This helps prevent interference from internal keyboard events
        self.suppress_key_events = False
        
        # Set up keyboard listener
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        # Start the listener in a separate thread
        self.listener_thread = None
    
    def start(self):
        """Start the keyboard listener."""
        if not self.listener.is_alive():
            self.listener.start()
            self.logger.info("Keyboard listener started")
    
    def start_listening(self):
        """Alias for start() to maintain compatibility."""
        self.start()
    
    def stop(self):
        """Stop the keyboard listener."""
        if self.listener.is_alive():
            self.listener.stop()
            self.logger.info("Keyboard listener stopped")
    
    def stop_listening(self):
        """Alias for stop() to maintain compatibility."""
        self.stop()
    
    def _parse_shortcut_key(self, shortcut_str):
        """
        Parse shortcut key string into a set of keys.
        
        Args:
            shortcut_str (str): Shortcut key string (e.g., "ctrl+alt+a")
            
        Returns:
            set: Set of key objects
        """
        parts = shortcut_str.lower().split('+')
        keys = set()
        
        for part in parts:
            if part == 'ctrl':
                keys.add(keyboard.Key.ctrl)
            elif part == 'alt':
                keys.add(keyboard.Key.alt)
            elif part == 'shift':
                keys.add(keyboard.Key.shift)
            elif len(part) == 1:
                # For single character keys
                keys.add(part)
            else:
                # Try to get key from keyboard.Key
                try:
                    key = getattr(keyboard.Key, part)
                    keys.add(key)
                except AttributeError:
                    self.logger.warning(f"Unknown key in shortcut: {part}")
        
        return keys
    
    def _on_key_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: The key that was pressed
        """
        # Skip processing if key events are suppressed
        if self.suppress_key_events:
            return
            
        try:
            # Convert key to a comparable format
            if isinstance(key, keyboard.Key):
                pressed_key = key
            else:
                # Handle potential AttributeError for special keys
                try:
                    pressed_key = key.char
                except AttributeError:
                    # If key doesn't have a char attribute, use the key object itself
                    pressed_key = key
            
            # Skip processing if the pressed key is not hashable
            # This prevents errors when slice objects or other non-hashable types are encountered
            if not isinstance(pressed_key, (str, keyboard.Key)) or not hasattr(pressed_key, '__hash__') or pressed_key.__hash__ is None:
                self.logger.warning(f"Skipping non-hashable key: {repr(pressed_key)}")
                return
            
            # Add to currently pressed keys
            self.currently_pressed.add(pressed_key)
            
            # Check if shortcut keys are all pressed and not already active
            if all(k in self.currently_pressed for k in self.keys) and not self.shortcut_active:
                self.shortcut_active = True
                if self.on_press_callback:
                    self.logger.info("Shortcut key combination pressed")
                    self.on_press_callback()
                    
        except Exception as e:
            # Handle errors safely to prevent listener crashes
            try:
                # First attempt to get a string representation using repr()
                # This safely handles complex objects like slice()
                error_msg = repr(e)
                # Truncate if too long
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                self.logger.error(f"Error in key press handler: {error_msg}")
            except:
                # Fallback if anything goes wrong during error formatting
                self.logger.error("Error in key press handler: Unable to format error message")
    
    def _on_key_release(self, key):
        """
        Handle key release events.
        
        Args:
            key: The key that was released
        """
        # Skip processing if key events are suppressed
        if self.suppress_key_events:
            return
            
        try:
            # Convert key to a comparable format
            if isinstance(key, keyboard.Key):
                released_key = key
            else:
                # Handle potential AttributeError for special keys
                try:
                    released_key = key.char
                except AttributeError:
                    # If key doesn't have a char attribute, use the key object itself
                    released_key = key
            
            # Skip processing if the released key is not hashable
            # This prevents errors when slice objects or other non-hashable types are encountered
            if not isinstance(released_key, (str, keyboard.Key)) or not hasattr(released_key, '__hash__') or released_key.__hash__ is None:
                self.logger.warning(f"Skipping non-hashable key: {repr(released_key)}")
                return
            
            # Remove from currently pressed keys
            if released_key in self.currently_pressed:
                self.currently_pressed.remove(released_key)
            
            # If shortcut was active and any key from shortcut is released
            if self.shortcut_active and any(k not in self.currently_pressed for k in self.keys):
                self.shortcut_active = False
                if self.on_release_callback:
                    self.logger.info("Shortcut key combination released")
                    try:
                        self.on_release_callback()
                    except Exception as callback_error:
                        # Log the specific error in the callback function
                        self.logger.error(f"Error in release callback function: {callback_error}")
                
        except Exception as e:
            # Handle errors safely to prevent listener crashes
            try:
                # First attempt to get a string representation using repr()
                # This safely handles complex objects like slice()
                error_msg = repr(e)
                # Truncate if too long
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                self.logger.error(f"Error in key release handler: {error_msg}")
            except:
                # Fallback if anything goes wrong during error formatting
                self.logger.error("Error in key release handler: Unable to format error message")