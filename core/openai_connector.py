import logging
import os
import base64
import json
import requests
from core.model_connector import ModelConnector

class OpenAIConnector(ModelConnector):
    """Connector for OpenAI models."""
    
    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.api_key = config_manager.get("models", "providers", "openai", "api_key", default="")
        self.model_name = config_manager.get("models", "providers", "openai", "model", default="gpt-4o")
        self.temperature = config_manager.get("ai", "temperature", default=0.2)
        self.max_tokens = config_manager.get("ai", "max_tokens", default=1024)
        self.system_prompt = self._load_system_prompt()
        
        if not self.api_key:
            self.logger.warning("No OpenAI API key provided. Please set one in the config file.")
    
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
        Process a query with OpenAI model, including screenshot data.
        
        Args:
            question (str): User's question
            context_data (bytes): Screenshot image data
            conversation_history (str, optional): Previous conversation history
            
        Returns:
            str: Model's response text
        """
        if not self.api_key:
            error_msg = "OpenAI API key not configured. Please add your API key to the config file."
            self.logger.error(error_msg)
            return error_msg
        
        try:
            # Convert image to base64
            base64_image = base64.b64encode(context_data).decode('utf-8')
            
            # Generate context from conversation history if provided
            context = ""
            if conversation_history and len(conversation_history) > 0:
                context = "Previous conversation:\n" + conversation_history
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Build the messages array
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history if available
            if context:
                messages.append({"role": "system", "content": f"Context: {context}"})
            
            # Add the user's question and image
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"User's question (referring to the attached screenshot): {question}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            })
            
            # Create the API request data
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # Make the API call
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(request_data)
            )
            
            # Parse the response
            if response.status_code == 200:
                result = response.json()
                raw_response = result['choices'][0]['message']['content']
                self.logger.info("Received response from OpenAI API")
                return raw_response
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return error_msg
            
        except Exception as e:
            error_msg = f"Error processing query with OpenAI model: {e}"
            self.logger.error(error_msg)
            return error_msg 