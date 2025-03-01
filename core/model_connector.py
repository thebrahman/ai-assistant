import logging
from abc import ABC, abstractmethod

class ModelConnector(ABC):
    """Base class for AI model connectors."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def process_query(self, question, context_data, conversation_history=None):
        """
        Process a query with AI model.
        
        Args:
            question (str): User's question
            context_data (bytes/dict): Data providing context (e.g., screenshot)
            conversation_history (str, optional): Previous conversation history
            
        Returns:
            str: Model's response text
        """
        raise NotImplementedError("Subclasses must implement this method") 