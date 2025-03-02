import logging
import google.generativeai as genai
from PIL import Image
import io
import os
import json
from datetime import datetime
from core.model_connector import ModelConnector
from logging.handlers import RotatingFileHandler

# Create a dedicated logger for LLM responses
llm_logger = logging.getLogger("llm_responses")

class GeminiConnector(ModelConnector):
    """Connector for Google's Gemini model."""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.api_key = config_manager.get_gemini_api_key()
        self.model_name = config_manager.get("models", "providers", "gemini", "model", default="gemini-1.5-flash")
        self.temperature = config_manager.get("ai", "temperature", default=0.2)
        self.max_tokens = config_manager.get("ai", "max_tokens", default=1024)
        self.system_prompt = self._load_system_prompt()
        
        # LLM response logging configuration
        self.log_llm_responses = config_manager.get("logging", "log_llm_responses", default=True)
        self.llm_log_file = config_manager.get("logging", "llm_log_file", default="logs/llm_responses.jsonl")
        self.max_log_size = config_manager.get("logging", "max_log_size", default=10485760)  # 10MB
        self.backup_count = config_manager.get("logging", "backup_count", default=5)
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.llm_log_file), exist_ok=True)
        
        # Configure the LLM response logger if enabled
        if self.log_llm_responses:
            # Remove any existing handlers
            for handler in llm_logger.handlers[:]:
                llm_logger.removeHandler(handler)
                
            # Add rotating file handler
            llm_file_handler = RotatingFileHandler(
                self.llm_log_file,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count
            )
            llm_file_handler.setLevel(logging.INFO)
            llm_formatter = logging.Formatter('%(message)s')
            llm_file_handler.setFormatter(llm_formatter)
            llm_logger.addHandler(llm_file_handler)
            llm_logger.setLevel(logging.INFO)
            
            self.logger.info(f"LLM response logging enabled to {self.llm_log_file}")
        
        # Initialize Gemini API
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.logger.info(f"Initialized Gemini API with model: {self.model_name}")
        else:
            self.logger.warning("No Gemini API key provided. Please set one in the config file.")
    
    def _load_system_prompt(self):
        """
        Load system prompt from file specified in config.
        
        Returns:
            str: System prompt text or default prompt if file not found
        """
        prompt_file = self.config_manager.get("ai", "system_prompt_file", default="prompts/system_prompt.md")
        
        # Default prompt in case file is not found
        default_prompt = (
            "You are an AI assistant that analyzes screenshots and user queries. "
            "Provide structured responses in JSON format with speech, notes, macro, and clipboard fields."
        )
        
        try:
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as file:
                    prompt = file.read().strip()
                self.logger.info(f"Loaded system prompt from {prompt_file}")
                return prompt
            else:
                self.logger.warning(f"System prompt file not found: {prompt_file}. Using default prompt.")
                return default_prompt
        except Exception as e:
            self.logger.error(f"Error loading system prompt: {e}. Using default prompt.")
            return default_prompt
    
    def process_query(self, question, context_data, conversation_history=None):
        """
        Process a query with the Gemini model, including context data.
        
        Args:
            question (str): User's question
            context_data (bytes): Screenshot image data
            conversation_history (str, optional): Previous conversation history
            
        Returns:
            str: Model's response text
        """
        if not self.api_key:
            error_msg = "Gemini API key not configured. Please add your API key to the config file."
            self.logger.error(error_msg)
            return error_msg
        
        try:
            # Load screenshot data as PIL Image
            image = Image.open(io.BytesIO(context_data))
            
            # Generate context from conversation history if provided
            context = ""
            if conversation_history and len(conversation_history) > 0:
                context = "Previous conversation:\n" + conversation_history + "\n\n"
            
            # Set up the model
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )
            
            # Construct the prompt with system prompt
            prompt = f"{self.system_prompt}\n\n{context}User's question (referring to the attached screenshot): {question}"
            
            # Generate response with both text and image input
            response = model.generate_content([prompt, image])
            
            raw_response = response.text
            self.logger.info("Received response from Gemini API")
            
            # Log the LLM response if logging is enabled
            if self.log_llm_responses:
                self._log_llm_response(question, raw_response)
            
            return raw_response
            
        except Exception as e:
            error_msg = f"Error processing query with Gemini model: {e}"
            self.logger.error(error_msg)
            return error_msg
    
    def _log_llm_response(self, question, response):
        """
        Log the LLM question and response to a dedicated log file.
        
        Args:
            question (str): The user's question
            response (str): The raw LLM response
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "temperature": self.temperature,
                "question": question,
                "response": response
            }
            
            # Log as a single JSON line for easy parsing
            llm_logger.info(json.dumps(log_entry, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Error logging LLM response: {e}") 