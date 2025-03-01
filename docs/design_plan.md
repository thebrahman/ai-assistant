# AI Assistant Enhancement Design Plan

## Current Architecture Analysis

The current AI Assistant application has the following components:

1. **ConfigManager**: Loads and manages configuration from YAML files
2. **InputManager**: Handles keyboard shortcuts via pynput
3. **ScreenshotCapture**: Captures screenshots of the active window
4. **AudioManager**: Handles audio recording, STT via Groq, and TTS via gTTS
5. **AIConnector**: Processes queries with Gemini API
6. **SessionManager**: Manages conversation history in markdown files
7. **AIAssistant**: Main class orchestrating all components

The application flow:

1. User holds keyboard shortcut (ctrl+alt+a)
2. App captures screenshot and records audio
3. On release, audio is transcribed to text
4. Question + screenshot are sent to Gemini
5. Answer is spoken via TTS and saved to markdown history

## Enhancement Requirements

1. **Structured JSON Output**
   - Structure responses with specific fields:
     - `speech`: Content for text-to-speech
     - `notes`: Content to save to notes.json
     - `macro`: Keyboard actions to execute
     - `clipboard`: Content to copy to clipboard

2. **Macro Execution with Confirmation**
   - Config option to toggle auto-execution of keyboard shortcuts
   - Notification system for user confirmation (Y/N)
   - Timeout for confirmation responses

3. **Extensible Architecture**
   - Support for adding new tools, agents, and LLM models
   - Plugin system for future extensions

## Design Plan

### 1. Configuration Extensions

Add new configuration options to `config.yaml`:

```yaml
# New configuration section
actions:
  auto_execute: false  # Whether to auto-execute keyboard shortcuts
  confirmation_timeout: 10  # Seconds to wait for confirmation
  notes_file: "notes.json"  # Path to the notes file

# Model providers configuration
models:
  default: "gemini"  # Default model provider
  providers:
    gemini:
      enabled: true
      model: "gemini-2.0-flash"
      api_key: "YOUR_GEMINI_API_KEY"
    openai:
      enabled: false
      model: "gpt-4o"
      api_key: "YOUR_OPENAI_API_KEY"

# Plugin configuration
plugins:
  directory: "plugins"
  enabled_plugins: []  # List of enabled plugins
```

### 2. New Core Components

#### ResponseProcessor

The ResponseProcessor parses and validates structured JSON responses from the LLM and routes different components to appropriate handlers.

```python
class ResponseProcessor:
    """Processes structured responses from LLM."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.action_manager = ActionManager(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        self.logger = logging.getLogger(__name__)
    
    def process_response(self, response_text, question):
        """
        Process a structured response from the LLM.
        
        Args:
            response_text (str): Raw response text from LLM
            question (str): Original user question
            
        Returns:
            dict: Processed results and actions taken
        """
        try:
            # Try to parse as JSON
            structured_response = self._extract_json(response_text)
            
            # If parsing fails, treat as plain text for speech
            if not structured_response:
                return {
                    "speech": response_text,
                    "raw_response": response_text,
                    "structured": False,
                    "actions_performed": []
                }
            
            # Validate required fields
            if "speech" not in structured_response:
                structured_response["speech"] = "I've processed your request but don't have anything specific to say."
            
            # Execute actions based on the response
            actions_performed = self.action_manager.execute_actions(structured_response, question)
            
            # Add metadata to the result
            result = {
                **structured_response,
                "raw_response": response_text,
                "structured": True,
                "actions_performed": actions_performed
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            return {
                "speech": f"I encountered an error processing the response: {str(e)}",
                "raw_response": response_text,
                "structured": False,
                "actions_performed": []
            }
    
    def _extract_json(self, text):
        """
        Extract JSON from text, handling various formats.
        
        Args:
            text (str): Text that may contain JSON
            
        Returns:
            dict: Extracted JSON or None if not found/invalid
        """
        # Implementation to extract JSON (handling various formats and code blocks)
```

#### ActionManager

The ActionManager executes various action types (clipboard, keyboard, notes) based on the structured response.

```python
class ActionManager:
    """Manages execution of various actions from AI responses."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.clipboard_util = ClipboardUtil()
        self.keyboard_automation = KeyboardAutomation()
        self.notes_manager = NotesManager(config_manager)
        self.notification_manager = NotificationManager(config_manager)
        self.auto_execute = config_manager.get("actions", "auto_execute", False)
        self.logger = logging.getLogger(__name__)
    
    def execute_actions(self, parsed_response, original_question):
        """
        Execute the actions in the parsed response.
        
        Args:
            parsed_response (dict): Structured response with actions
            original_question (str): Original user question
            
        Returns:
            list: Actions that were performed
        """
        actions_performed = []
        
        # Handle clipboard content
        if "clipboard" in parsed_response and parsed_response["clipboard"]:
            content = parsed_response["clipboard"]
            if self.clipboard_util.copy_to_clipboard(content):
                actions_performed.append({"type": "clipboard", "content": content})
        
        # Handle notes
        if "notes" in parsed_response and parsed_response["notes"]:
            notes_data = parsed_response["notes"]
            if isinstance(notes_data, dict):
                title = notes_data.get("title", f"Note from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                content = notes_data.get("content", "")
                
                if content:
                    self.notes_manager.add_note(title, content, original_question)
                    actions_performed.append({"type": "notes", "title": title})
        
        # Handle macro execution
        if "macro" in parsed_response and parsed_response["macro"]:
            macro_data = parsed_response["macro"]
            
            if isinstance(macro_data, dict):
                keys = macro_data.get("keys", "")
                description = macro_data.get("description", "Execute keyboard shortcut")
                
                if keys:
                    # Check if we need confirmation
                    execute = self.auto_execute
                    
                    if not execute:
                        # Request confirmation
                        confirmation_message = f"Execute keyboard shortcut: {description} ({keys})"
                        execute = self.notification_manager.show_confirmation(confirmation_message)
                    
                    # Execute if confirmed or auto-execute is enabled
                    if execute:
                        if self.keyboard_automation.execute_sequence(keys):
                            actions_performed.append({
                                "type": "macro", 
                                "keys": keys, 
                                "description": description
                            })
        
        return actions_performed
```

#### NotificationManager

The NotificationManager displays notifications for user confirmation and handles user input.

```python
class NotificationManager:
    """Handles displaying notifications and getting user confirmation."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.timeout = config_manager.get("actions", "confirmation_timeout", 10)
        self.logger = logging.getLogger(__name__)
    
    def show_confirmation(self, action_description):
        """
        Show confirmation dialog and wait for user input.
        
        Args:
            action_description (str): Description of the action
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        print("\n" + "="*50)
        print(f"CONFIRMATION REQUIRED: {action_description}")
        print(f"Press Y to execute or N to cancel (timeout in {self.timeout} seconds)")
        print("="*50)
        
        # Use a separate thread to handle timeout
        result = {"confirmed": False}
        
        def get_input():
            try:
                while True:
                    user_input = input().strip().lower()
                    if user_input == 'y':
                        result["confirmed"] = True
                        return
                    elif user_input == 'n':
                        result["confirmed"] = False
                        return
                    else:
                        print("Invalid input. Press Y to execute or N to cancel.")
            except Exception as e:
                self.logger.error(f"Error getting confirmation input: {e}")
                result["confirmed"] = False
        
        # Start input thread
        input_thread = threading.Thread(target=get_input)
        input_thread.daemon = True
        input_thread.start()
        
        # Wait for input or timeout
        input_thread.join(timeout=self.timeout)
        
        if input_thread.is_alive():
            # Timeout occurred
            print("Confirmation timeout - action cancelled")
            return False
        
        return result["confirmed"]
```

#### NotesManager

The NotesManager manages saving and retrieving notes from a JSON file.

```python
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
        """Get recent notes."""
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Return most recent notes
            notes = data.get("notes", [])
            return notes[-limit:] if limit > 0 else notes
            
        except Exception as e:
            self.logger.error(f"Error getting notes: {e}")
            return []
```

#### ClipboardUtil

The ClipboardUtil handles copying content to the clipboard.

```python
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
```

#### KeyboardAutomation

The KeyboardAutomation handles executing keyboard shortcuts and sequences.

```python
class KeyboardAutomation:
    """Utility for executing keyboard shortcuts."""
    
    def __init__(self):
        from pynput.keyboard import Key, Controller
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
            # ... other key mappings
        }
        self.logger = logging.getLogger(__name__)
    
    def _get_key(self, key_str):
        """Convert string key representation to pynput Key object."""
        key_str = key_str.lower().strip()
        
        if key_str in self.key_mapping:
            return self.key_mapping[key_str]
        elif len(key_str) == 1:
            return key_str
        else:
            self.logger.warning(f"Unknown key: {key_str}")
            return None
    
    def press_key_combination(self, shortcut):
        """Press a key combination like Ctrl+Alt+T."""
        try:
            # Parse the shortcut and press keys
            # Implementation details...
            return True
        except Exception as e:
            self.logger.error(f"Error executing keyboard shortcut: {e}")
            return False
    
    def execute_sequence(self, sequence):
        """Execute a sequence of keyboard actions (e.g., "Ctrl+B->X")."""
        try:
            # Split and execute sequence
            # Implementation details...
            return True
        except Exception as e:
            self.logger.error(f"Error executing keyboard sequence: {e}")
            return False
```

### 3. Model Abstraction Layer

Create a model abstraction layer to support multiple LLM providers:

```python
class ModelConnector:
    """Base class for AI model connectors."""
    
    def process_query(self, question, context_data, conversation_history=None):
        """Process a query with AI model."""
        raise NotImplementedError("Subclasses must implement this method")

class GeminiConnector(ModelConnector):
    """Connector for Google's Gemini model."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Initialize Gemini-specific settings
        
    def process_query(self, question, context_data, conversation_history=None):
        # Gemini-specific implementation
        pass

class OpenAIConnector(ModelConnector):
    """Connector for OpenAI models."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        # Initialize OpenAI-specific settings
        
    def process_query(self, question, context_data, conversation_history=None):
        # OpenAI-specific implementation
        pass

class ModelFactory:
    """Factory class to create appropriate model connectors."""
    
    @staticmethod
    def create_connector(config_manager):
        """Create the appropriate model connector based on configuration."""
        default_provider = config_manager.get("models", "default", "gemini")
        
        if default_provider == "gemini":
            return GeminiConnector(config_manager)
        elif default_provider == "openai":
            return OpenAIConnector(config_manager)
        else:
            raise ValueError(f"Unsupported model provider: {default_provider}")
```

### 4. Plugin Architecture

Create a plugin system for extensibility:

```python
class Plugin:
    """Base class for plugins."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
    def initialize(self):
        """Initialize the plugin."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def execute(self, context):
        """Execute the plugin with the given context."""
        raise NotImplementedError("Subclasses must implement this method")

class PluginManager:
    """Manages loading and running plugins."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugins = {}
        self.logger = logging.getLogger(__name__)
        self.load_plugins()
    
    def load_plugins(self):
        """Load all enabled plugins."""
        plugin_dir = self.config_manager.get("plugins", "directory", "plugins")
        enabled_plugins = self.config_manager.get("plugins", "enabled_plugins", [])
        
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir, exist_ok=True)
            return
        
        # Load each enabled plugin
        for plugin_name in enabled_plugins:
            try:
                # Dynamic import and initialization
                module_path = f"{plugin_dir}.{plugin_name}"
                module = importlib.import_module(module_path)
                
                # Find the plugin class (convention: main class has the same name as the module)
                plugin_class = getattr(module, plugin_name)
                plugin_instance = plugin_class(self.config_manager)
                plugin_instance.initialize()
                
                self.plugins[plugin_name] = plugin_instance
                self.logger.info(f"Loaded plugin: {plugin_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading plugin {plugin_name}: {e}")
    
    def execute_plugin(self, plugin_name, context):
        """Execute a specific plugin."""
        if plugin_name in self.plugins:
            try:
                return self.plugins[plugin_name].execute(context)
            except Exception as e:
                self.logger.error(f"Error executing plugin {plugin_name}: {e}")
                return None
        else:
            self.logger.warning(f"Plugin not found: {plugin_name}")
            return None
```

### 5. Updated System Prompt

Update the system prompt to instruct the model to return structured responses:

```markdown
# You are an AI assistant that analyzes screenshots and user queries

Please provide responses in the following JSON structure:

```json
{
  "speech": "What to speak to the user (keep this concise and conversational)",
  "notes": {
    "title": "Optional note title",
    "content": "Content to save to notes.json (optional)"
  },
  "macro": {
    "description": "Description of what the macro does",
    "keys": "keyboard shortcut sequence like ctrl+b->%"
  },
  "clipboard": "Content to copy to clipboard (optional)"
}
```

When responding:

- Always include the "speech" field
- Only include other fields when relevant to the user's request
- For keyboard shortcuts, use -> to separate sequential keypresses
- Use "+" for simultaneous key presses (e.g., "ctrl+b")
- Wrap your JSON in triple backticks with json language identifier

Keep the speech content concise and optimized for text-to-speech:

- Use simple, conversational language
- Avoid lengthy explanations unless specifically requested
- Focus on directly answering the user's question
- When describing visual elements, be clear but efficient

### 6. Integration with Existing Components

Update the AIConnector to use the new structured response approach:

```python
class AIConnector:
    """Handles interactions with AI models."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.model_connector = ModelFactory.create_connector(config_manager)
        self.response_processor = ResponseProcessor(config_manager)
        self.system_prompt = self._load_system_prompt()
        self.logger = logging.getLogger(__name__)
    
    def process_query(self, question, screenshot_data, conversation_history=None):
        """
        Process a query with the AI model, including screenshot data.
        
        Args:
            question (str): User's question
            screenshot_data (bytes): Screenshot image data
            conversation_history (list, optional): Previous conversation history
            
        Returns:
            dict: Processed response with speech and action results
        """
        try:
            # Get raw response from the model
            raw_response = self.model_connector.process_query(
                question, 
                screenshot_data, 
                conversation_history
            )
            
            # Process structured response
            processed_response = self.response_processor.process_response(
                raw_response,
                question
            )
            
            return processed_response
            
        except Exception as e:
            error_msg = f"Error processing query: {e}"
            self.logger.error(error_msg)
            
            return {
                "speech": f"Sorry, I encountered an error: {str(e)}",
                "raw_response": error_msg,
                "structured": False,
                "actions_performed": []
            }
```

Update the main application to use the enhanced components:

```python
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
    
    # Process with AI if we have a screenshot
    if self.current_screenshot:
        print("Sending to AI model...")
        response = self.ai_connector.process_query(
            question,
            self.current_screenshot,
            history
        )
        
        # Get the speech content for TTS
        speech_content = response.get("speech", "")
        
        print(f"Answer: \"{speech_content[:100]}{'...' if len(speech_content) > 100 else ''}\"")
        
        # Show actions performed
        actions = response.get("actions_performed", [])
        if actions:
            print("Actions performed:")
            for action in actions:
                action_type = action.get("type", "unknown")
                if action_type == "clipboard":
                    print("- Copied content to clipboard")
                elif action_type == "macro":
                    print(f"- Executed keyboard shortcut: {action.get('description', '')}")
                elif action_type == "notes":
                    print(f"- Added note: {action.get('title', '')}")
        
        # Save to markdown
        raw_response = response.get("raw_response", speech_content)
        self.session_manager.add_interaction(question, raw_response)
        
        # Speak the answer
        self.audio_manager.speak_text(speech_content)
    else:
        print("Error: No screenshot captured")
```

## Implementation Order

To implement these enhancements in a phased approach:

1. **Phase 1: Core Action Infrastructure**
   - Add ClipboardUtil for clipboard functionality
   - Add KeyboardAutomation for keyboard shortcuts
   - Add NotificationManager for confirmations
   - Update config with action settings

   **Starting File Context:**
   - config/config_manager.py
   - config/config.example.yaml
   - core/input_manager.py (for understanding keyboard handling)

   **Finished File Context:**
   - config/config.example.yaml (updated with new action settings)
   - config/config.yaml (user's config to update)
   - core/clipboard_util.py (new)
   - core/keyboard_automation.py (new)
   - core/notification_manager.py (new)

2. **Phase 2: Structured Output**
   - Implement ResponseProcessor for JSON parsing
   - Update the system prompt
   - Add NotesManager for note-taking
   - Update AIConnector to use structured responses

   **Starting File Context:**
   - core/ai_connector.py
   - prompts/system_prompt.md
   - app.py (for understanding the response flow)
   - Phase 1 completed files

   **Finished File Context:**
   - core/response_processor.py (new)
   - core/notes_manager.py (new)
   - prompts/system_prompt.md (updated for structured output)
   - core/ai_connector.py (modified to use structured responses)

3. **Phase 3: Extensibility**
   - Implement the model abstraction layer
   - Add the plugin architecture
   - Create model-specific connectors

   **Starting File Context:**
   - core/ai_connector.py
   - app.py
   - Phase 1 and 2 completed files

   **Finished File Context:**
   - core/model_connector.py (new base connector)
   - core/model_factory.py (new)
   - core/gemini_connector.py (new)
   - core/openai_connector.py (new)
   - core/plugin_manager.py (new)
   - plugins/ (new directory)
   - app.py (modified to use model factory)

## Testing Considerations

For each new component:
1. Unit tests for individual functionality
2. Integration tests for component interaction
3. End-to-end tests for full flow
4. Error handling tests for edge cases

## Security Considerations

1. **Macro Execution**: Always require confirmation for potentially dangerous actions
2. **Input Validation**: Validate all structured input before processing
3. **Plugin Security**: Implement sandboxing for plugins
4. **Config Validation**: Validate configuration at startup

