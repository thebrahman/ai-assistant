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
        # Create logger first so it's available throughout initialization
        self.logger = logging.getLogger("AIAssistant")
        
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
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        os.makedirs("config", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("prompts", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("notes", exist_ok=True)
        self.logger.info("Ensured required directories exist (config, sessions, prompts, logs, notes)")
    
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
            
            # Suppress key events during AI processing and TTS to prevent conflicts
            self.input_manager.suppress_key_events = True
            
            try:
                # Get the processed response (dictionary)
                response = self.ai_connector.process_query(
                    question,
                    self.current_screenshot,
                    history
                )
                
                # Extract the speech content for display and TTS
                speech_content = response.get("speech", "")
                
                # Display a preview of the speech content
                print(f"Answer: \"{speech_content[:100]}{'...' if len(speech_content) > 100 else ''}\"")
                
                # Display any actions performed
                actions = response.get("actions_performed", [])
                if actions:
                    print("Actions performed:")
                    for action in actions:
                        action_type = action.get("action", "unknown")
                        if action_type == "clipboard":
                            print("- Copied content to clipboard")
                        elif action_type == "macro":
                            print(f"- Executed keyboard shortcut: {action.get('result', '')}")
                
                # Save the raw response to the session
                raw_response = response.get("raw_response", speech_content)
                self.session_manager.add_interaction(question, raw_response)
                
                # Speak the speech content
                self.audio_manager.speak_text(speech_content)
            finally:
                # Always restore key event processing when done
                self.input_manager.suppress_key_events = False
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





