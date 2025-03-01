# AI Assistant

A simple, efficient AI assistant that captures screenshots, listens to voice queries, and provides answers using Google's Gemini model.

## Features

- Press and hold a keyboard shortcut to activate the assistant
- Automatically captures the active window as a screenshot
- Records audio while the shortcut is held down
- Transcribes speech to text using Groq API
- Sends the question and screenshot to Google's Gemini model
- Saves conversations to markdown files for future reference
- Speaks responses using text-to-speech

## Installation

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai-assistant.git
   cd ai-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using uv:
   ```bash
   uv add -r requirements.txt
   ```

3. Configure the application:
   - Copy `config/config.yaml.example` to `config/config.yaml` (or create it if it doesn't exist)
   - Edit `config/config.yaml` to add your Gemini API key and Groq API key
   - Configure other settings as needed

## Usage

### Starting the Assistant

```bash
python app.py
```

Or using uv:
```bash
uv run app.py
```

### Using the Assistant

1. Press and hold the configured keyboard shortcut (default: `ctrl+alt+a`)
2. While holding the shortcut, speak your question
3. Release the shortcut when finished speaking
4. The assistant will:
   - Process your question
   - Display the transcribed text
   - Send the question and screenshot to Gemini
   - Speak the answer using text-to-speech
   - Save the interaction to the current session file

### Creating a New Session

To create a new conversation session:

```bash
python utils/new_session.py
```

## Configuration

Edit `config/config.yaml` to customize the following settings:

- **Keyboard shortcut**: Change the key combination to activate the assistant
- **Speech settings**: Configure STT (Groq API) and TTS options
- **AI settings**: Set the Gemini model, API key, and parameters
- **Session settings**: Control how conversation sessions are managed
- **Screenshot settings**: Configure screenshot format and quality

## Project Structure

```
ai_assistant/
├── config/
│   ├── config.yaml          # Configuration file
│   └── config_manager.py    # Configuration management
├── core/
│   ├── input_manager.py     # Keyboard shortcut handling
│   ├── screenshot.py        # Active window screenshots
│   ├── audio_manager.py     # Audio recording, STT, TTS
│   ├── ai_connector.py      # Gemini API interaction
│   └── session_manager.py   # Markdown file management
├── utils/
│   └── new_session.py       # Utility to create new sessions
├── prompts/
│   └── system_prompt.md     # System prompt for Gemini
├── sessions/                # Where conversation files are stored
├── app.py                   # Main application entry point
└── README.md                # This file
```

## Key Components

- **InputManager**: Handles keyboard shortcuts using pynput
- **ScreenshotCapture**: Captures screenshots of the active window
- **AudioManager**: Records audio, transcribes with Groq API, and provides TTS
- **AIConnector**: Processes queries with Google's Gemini API
- **SessionManager**: Manages conversation history in markdown files
- **ConfigManager**: Handles application configuration

## Dependencies

- **pynput**: Keyboard input handling
- **mss** or similar: Screen capture
- **sounddevice/soundfile**: Audio recording
- **groq**: Speech-to-text via Groq API
- **google-generativeai**: Gemini API integration
- **TTS libraries**: Text-to-speech playback
- **pillow**: Image processing
- **pyyaml**: Configuration file parsing

## Future Enhancements

- Add support for multiple AI agents
- Implement tools and function calling
- Add a graphical user interface
- Improve conversation context handling
- Add support for custom TTS voices
- Enhance active window detection for screenshots
- Improve error handling and recovery

## License

MIT