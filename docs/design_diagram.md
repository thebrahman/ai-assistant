```mermaid
classDiagram
    %% Main Application Class
    class AIAssistant {
        -ConfigManager config_manager
        -InputManager input_manager
        -ScreenshotCapture screenshot_capture
        -AudioManager audio_manager
        -AIConnector ai_connector
        -SessionManager session_manager
        -current_screenshot
        -logger
        +__init__(config_path)
        +start()
        +_setup_keyboard_listener()
        +_handle_shortcut_press()
        +_handle_shortcut_release()
        +_shutdown()
        +_handle_signal(sig, frame)
    }

    %% Configuration
    class ConfigManager {
        -config_path
        -config
        +__init__(config_path)
        +_load_config()
        +_setup_logging()
        +_ensure_directories()
        +get(section, *path_components, default)
        +get_shortcut_key()
        +get_session_file()
        +get_new_session_on_startup()
        +get_gemini_api_key()
    }

    %% Core Components
    class InputManager {
        -config_manager
        -shortcut_key
        -keys
        -currently_pressed
        -shortcut_active
        -suppress_key_events
        -listener
        -listener_thread
        -on_press_callback
        -on_release_callback
        +__init__(config_manager, on_press, on_release)
        +start()
        +start_listening()
        +stop()
        +stop_listening()
        +_parse_shortcut_key(shortcut_str)
        +_on_key_press(key)
        +_on_key_release(key)
    }

    class ScreenshotCapture {
        -config_manager
        -format
        -quality
        -logger
        +__init__(config_manager)
        +capture_active_window()
        +save_screenshot(path)
    }

    class AudioManager {
        -config_manager
        -stt_engine
        -stt_api_key
        -stt_model
        -tts_engine
        -tts_rate
        -tts_volume
        -tts_voice
        -channels
        -sample_rate
        -recording
        -frames
        -stream
        -logger
        +__init__(config_manager)
        +start_recording()
        +stop_recording()
        +transcribe_audio(audio_data)
        +_transcribe_with_groq(audio_data)
        +speak_text(text)
        +_speak_with_gtts(text)
    }

    class SessionManager {
        -config_manager
        -sessions_dir
        -current_session_file
        -logger
        +__init__(config_manager)
        +_get_session_file()
        +create_new_session()
        +get_conversation_history(max_entries)
        +add_interaction(question, answer)
    }

    %% AI Components
    class AIConnector {
        -config_manager
        -model_connector
        -response_processor
        -plugin_manager
        -logger
        +__init__(config_manager)
        +process_query(question, screenshot_data, conversation_history)
    }

    class ModelConnector {
        <<abstract>>
        -config_manager
        -logger
        +__init__(config_manager)
        +process_query(question, context_data, conversation_history)
    }

    class GeminiConnector {
        -config_manager
        -api_key
        -model_name
        -temperature
        -max_tokens
        -system_prompt
        -log_llm_responses
        -llm_log_file
        -max_log_size
        -backup_count
        -logger
        +__init__(config_manager)
        +_load_system_prompt()
        +process_query(question, context_data, conversation_history)
        +_log_llm_response(question, response)
    }

    class OpenAIConnector {
        -config_manager
        -api_key
        -model_name
        -temperature
        -max_tokens
        -system_prompt
        -logger
        +__init__(config_manager)
        +_load_system_prompt()
        +process_query(question, context_data, conversation_history)
    }

    class ModelFactory {
        <<static>>
        +create_connector(config_manager)
    }

    %% Response Processing Components
    class ResponseProcessor {
        -config_manager
        -action_manager
        -notification_manager
        -plugins_enabled
        -plugins_dir
        -templates_dir
        -log_llm_responses
        -logger
        +__init__(config_manager)
        +process_response(raw_response, query)
        +_extract_json(text)
        +_copy_to_clipboard(text)
        +_run_macro(macro_command)
        +_log_response_processing(query, raw_response, json_data)
        +_log_macro_processing(macro_data)
        +_log_processing_error(query, raw_response, error_msg)
    }

    class ActionManager {
        -config_manager
        -clipboard_util
        -keyboard_automation
        -notes_manager
        -notification_manager
        -auto_execute
        -logger
        +__init__(config_manager)
        +execute_actions(parsed_response, original_question)
    }

    class ClipboardUtil {
        -logger
        +__init__()
        +copy_to_clipboard(text)
    }

    class KeyboardAutomation {
        -keyboard
        -key_mapping
        -logger
        +__init__()
        +_get_key(key_str)
        +press_key_combination(shortcut)
        +execute_sequence(sequence)
    }

    class NotificationManager {
        -config_manager
        -timeout
        -logger
        +__init__(config_manager)
        +show_confirmation(action_description)
        +show_notification(message)
    }

    class NotesManager {
        -config_manager
        -notes_file
        -logger
        +__init__(config_manager)
        +_ensure_notes_file()
        +add_note(title, content, related_question)
        +get_notes(limit)
    }

    %% Plugin System
    class PluginManager {
        -config_manager
        -plugins
        -plugin_dir
        -logger
        +__init__(config_manager)
        +load_plugins()
        +execute_plugin(plugin_name, context)
        +get_available_plugins()
        +has_plugin(plugin_name)
    }

    class Plugin {
        <<abstract>>
        -config_manager
        -logger
        +__init__(config_manager)
        +initialize()
        +execute(context)
        +name
        +description
    }

    %% Relationships
    AIAssistant *-- ConfigManager
    AIAssistant *-- InputManager
    AIAssistant *-- ScreenshotCapture
    AIAssistant *-- AudioManager
    AIAssistant *-- SessionManager
    AIAssistant *-- AIConnector
    
    AIConnector *-- ModelConnector
    AIConnector *-- ResponseProcessor
    AIConnector *-- PluginManager
    
    ModelConnector <|-- GeminiConnector
    ModelConnector <|-- OpenAIConnector
    
    ModelFactory ..> ModelConnector : creates
    ModelFactory ..> GeminiConnector : creates
    ModelFactory ..> OpenAIConnector : creates
    
    ResponseProcessor *-- ActionManager
    ResponseProcessor *-- NotificationManager
    
    ActionManager *-- ClipboardUtil
    ActionManager *-- KeyboardAutomation
    ActionManager *-- NotesManager
    ActionManager *-- NotificationManager
    
    PluginManager o-- Plugin
``` 