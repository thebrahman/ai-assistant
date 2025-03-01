import os
import logging
import time
import threading
import signal
import sys
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from config.config_manager import ConfigManager
from core.screenshot import ScreenshotCapture
from core.audio_manager import AudioManager
from core.ai_connector import AIConnector
from core.session_manager import SessionManager
from core.input_manager import InputManager

class AIAssistant:
    """Main AI Assistant application."""
    
    def __init__(self, config_path="config/config.yaml"):
        # Ensure required directories exist
        self._ensure_directories()
        
        # Initialize components
        print("Initializing AI Assistant...")
        self.config_manager = ConfigManager(config_path)
        self.session_manager = SessionManager(self.config_manager)
        self.screenshot_capture = ScreenshotCapture(self.config_manager)
        self.audio_manager = AudioManager(self.config_manager)
        self.ai_connector = AIConnector(self.config_manager)
        
        # Initialize input manager with callbacks
        self.input_manager = InputManager(
            self.config_manager,
            on_press=self._handle_shortcut_press,
            on_release=self._handle_shortcut_release
        )
        
        # Internal state
        self.current_screenshot = None
        self.running = False
        
        # Set up signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # Create logger
        self.logger = logging.getLogger("AIAssistant")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        os.makedirs("config", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("prompts", exist_ok=True)
    
    def start(self):
        """Start the AI Assistant."""
        self.running = True
        
        # Get shortcut key for user information
        shortcut_key = self.config_manager.get_shortcut_key()
        
        print(f"AI Assistant started. Press and hold '{shortcut_key}' to activate.")
        print("Press Ctrl+C to exit.")
        
        # Start keyboard listener
        self.input_manager.start_listening()
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self._shutdown()
    
    def _shutdown(self):
        """Shut down the AI Assistant."""
        self.running = False
        print("\nShutting down AI Assistant...")
        
        # Clean up resources
        self.input_manager.stop_listening()
        
        print("Goodbye!")
    
    def _handle_shortcut_press(self):
        """Handle shortcut key press events."""
        self.logger.info("Shortcut pressed, starting capture")
        print("Assistant activated. Capturing screenshot...")
        
        # Capture screenshot
        self.current_screenshot = self.screenshot_capture.capture_active_window()
        
        # Start audio recording
        print("Listening... (release shortcut when done speaking)")
        self.audio_manager.start_recording()
    
    def _handle_shortcut_release(self):
        """Handle shortcut key release events."""
        self.logger.info("Shortcut released, processing query")
        print("Processing your question...")
        
        # Stop recording and get audio data
        audio_data = self.audio_manager.stop_recording()
        
        if audio_data is None or (isinstance(audio_data, np.ndarray) and audio_data.size == 0):
            print("No audio detected. Please try again.")
            return
        
        # Convert speech to text
        question = self.audio_manager.transcribe_audio(audio_data)
        
        if not question:
            print("Could not understand audio. Please try again.")
            return
        
        print(f"Your question: \"{question}\"")
        
        # Get conversation history
        history = self.session_manager.get_conversation_history()
        
        # Process with Gemini if we have a screenshot
        if self.current_screenshot:
            print("Sending to Gemini API...")
            answer = self.ai_connector.process_query(
                question,
                self.current_screenshot,
                history
            )
            
            print(f"Answer: \"{answer[:100]}{'...' if len(answer) > 100 else ''}\"")
            
            # Save to markdown
            self.session_manager.add_interaction(question, answer)
            
            # Speak the answer
            self.audio_manager.speak_text(answer)
        else:
            print("Error: No screenshot captured")
    
    def _handle_signal(self, sig, frame):
        """Handle termination signals."""
        self._shutdown()
        sys.exit(0)

if __name__ == "__main__":
    # Check if config file exists, if not print a warning
    if not os.path.exists("config/config.yaml"):
        print("Warning: config/config.yaml not found. Please create it before running the application.")
        print("You can use the template in config/config.yaml.example as a starting point.")
        sys.exit(1)
    
    # Initialize and start the AI Assistant
    assistant = AIAssistant()
    assistant.start()





