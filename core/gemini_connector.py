import logging
import google.generativeai as genai
from PIL import Image
import io
import os
from core.model_connector import ModelConnector

class GeminiConnector(ModelConnector):
    """Connector for Google's Gemini model."""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.api_key = config_manager.get_gemini_api_key()
        self.model_name = config_manager.get("models", "providers", "gemini", "model", "gemini-1.5-flash")
        self.temperature = config_manager.get("ai", "temperature", 0.2)
        self.max_tokens = config_manager.get("ai", "max_tokens", 1024)
        self.system_prompt = self._load_system_prompt()
        
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
        prompt_file = self.config_manager.get("ai", "system_prompt_file", "prompts/system_prompt.md")
        
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
            
            return raw_response
            
        except Exception as e:
            error_msg = f"Error processing query with Gemini model: {e}"
            self.logger.error(error_msg)
            return error_msg 