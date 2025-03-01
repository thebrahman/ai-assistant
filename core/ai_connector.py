import logging
import google.generativeai as genai
from PIL import Image
import io
import os

logger = logging.getLogger(__name__)

class AIConnector:
    """Handles interactions with AI models."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.api_key = config_manager.get_gemini_api_key()
        self.model_name = config_manager.get("ai", "model", "gemini-1.5-flash")
        self.temperature = config_manager.get("ai", "temperature", 0.2)
        self.max_tokens = config_manager.get("ai", "max_tokens", 1024)
        self.system_prompt = self._load_system_prompt()
        
        # Initialize response processor
        from core.response_processor import ResponseProcessor
        self.response_processor = ResponseProcessor(config_manager)
        
        # Initialize Gemini API
        if self.api_key:
            genai.configure(api_key=self.api_key)
            logger.info(f"Initialized Gemini API with model: {self.model_name}")
        else:
            logger.warning("No Gemini API key provided. Please set one in the config file.")
    
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
                logger.info(f"Loaded system prompt from {prompt_file}")
                return prompt
            else:
                logger.warning(f"System prompt file not found: {prompt_file}. Using default prompt.")
                return default_prompt
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}. Using default prompt.")
            return default_prompt
    
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
        if not self.api_key:
            error_msg = "Gemini API key not configured. Please add your API key to the config file."
            logger.error(error_msg)
            return {
                "speech": error_msg,
                "raw_response": error_msg,
                "structured": False,
                "actions_performed": []
            }
        
        try:
            # Load screenshot data as PIL Image
            image = Image.open(io.BytesIO(screenshot_data))
            
            # Generate context from conversation history if provided
            context = ""
            if conversation_history and len(conversation_history) > 0:
                # Keep it simple for the prototype
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
            logger.info("Received response from Gemini API")
            
            # Process the response with the ResponseProcessor
            processed_response = self.response_processor.process_response(raw_response, question)
            
            return processed_response
            
        except Exception as e:
            error_msg = f"Error processing query with AI model: {e}"
            logger.error(error_msg)
            
            return {
                "speech": f"Sorry, I encountered an error: {str(e)}",
                "raw_response": error_msg,
                "structured": False,
                "actions_performed": []
            }