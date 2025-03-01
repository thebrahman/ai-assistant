import logging
import time
from pynput.keyboard import Key, Controller

class KeyboardAutomation:
    """Utility for executing keyboard shortcuts."""
    
    def __init__(self):
        self.keyboard = Controller()
        self.key_mapping = {
            'ctrl': Key.ctrl,
            'alt': Key.alt,
            'shift': Key.shift,
            'cmd': Key.cmd,
            'command': Key.cmd,
            'meta': Key.cmd,
            'win': Key.cmd,
            'tab': Key.tab,
            'space': Key.space,
            'enter': Key.enter,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'esc': Key.esc,
            'escape': Key.esc,
            'home': Key.home,
            'end': Key.end,
            'pageup': Key.page_up,
            'pagedown': Key.page_down,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
        }
        self.logger = logging.getLogger(__name__)
    
    def _get_key(self, key_str):
        """
        Convert string key representation to pynput Key object.
        
        Args:
            key_str (str): String representation of a key
            
        Returns:
            Key or str: pynput Key object or character string
        """
        key_str = key_str.lower().strip()
        
        if key_str in self.key_mapping:
            return self.key_mapping[key_str]
        elif len(key_str) == 1:
            return key_str
        else:
            self.logger.warning(f"Unknown key: {key_str}")
            return None
    
    def press_key_combination(self, shortcut):
        """
        Press a key combination like Ctrl+Alt+T.
        
        Args:
            shortcut (str): Shortcut string like "ctrl+alt+t"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keys = shortcut.split('+')
            key_objects = [self._get_key(k) for k in keys]
            
            # Filter out None values
            key_objects = [k for k in key_objects if k is not None]
            
            if not key_objects:
                self.logger.error(f"No valid keys in shortcut: {shortcut}")
                return False
            
            # Press all keys in sequence
            for key in key_objects:
                self.keyboard.press(key)
            
            time.sleep(0.1)  # Small delay
            
            # Release all keys in reverse order
            for key in reversed(key_objects):
                self.keyboard.release(key)
            
            self.logger.info(f"Executed keyboard shortcut: {shortcut}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing keyboard shortcut: {e}")
            return False
    
    def execute_sequence(self, sequence):
        """
        Execute a sequence of keyboard actions (e.g., "Ctrl+B->X").
        
        Args:
            sequence (str): Sequence string like "ctrl+b->x"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Split the sequence by arrow notation
            steps = sequence.split('->')
            
            for step in steps:
                step = step.strip()
                
                # Check if it's a combination or single key
                if '+' in step:
                    # It's a key combination
                    if not self.press_key_combination(step):
                        return False
                else:
                    # It's a single key
                    key = self._get_key(step)
                    if key is None:
                        self.logger.error(f"Invalid key in sequence: {step}")
                        return False
                    
                    self.keyboard.press(key)
                    time.sleep(0.05)
                    self.keyboard.release(key)
                
                # Small delay between steps
                time.sleep(0.2)
            
            self.logger.info(f"Executed keyboard sequence: {sequence}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing keyboard sequence: {e}")
            return False 