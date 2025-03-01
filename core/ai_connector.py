import logging
from core.model_factory import ModelFactory

logger = logging.getLogger(__name__)

class AIConnector:
    """Handles interactions with AI models."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        # Initialize response processor
        from core.response_processor import ResponseProcessor
        self.response_processor = ResponseProcessor(config_manager)
        
        # Initialize plugin manager if enabled
        self.plugin_manager = None
        if config_manager.get("plugins", "enabled", False):
            from core.plugin_manager import PluginManager
            self.plugin_manager = PluginManager(config_manager)
            logger.info("Plugin system initialized")
        
        # Get the appropriate model connector
        try:
            self.model_connector = ModelFactory.create_connector(config_manager)
            logger.info(f"Initialized AI model connector: {self.model_connector.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize model connector: {e}")
            self.model_connector = None
    
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
        if not self.model_connector:
            error_msg = "AI model connector not initialized. Please check your configuration."
            logger.error(error_msg)
            return {
                "speech": error_msg,
                "raw_response": error_msg,
                "structured": False,
                "actions_performed": []
            }
        
        try:
            # Process query through the model connector
            raw_response = self.model_connector.process_query(
                question,
                screenshot_data,
                conversation_history
            )
            
            logger.info("Received raw response from model connector")
            
            # Process the response with the ResponseProcessor
            processed_response = self.response_processor.process_response(raw_response, question)
            
            # Run any plugins if enabled
            if self.plugin_manager and processed_response.get("structured", False):
                # Create context for plugins
                plugin_context = {
                    "question": question,
                    "processed_response": processed_response,
                    "conversation_history": conversation_history
                }
                
                # Check if response specifies any plugins to run
                if "plugins" in processed_response:
                    plugins_to_run = processed_response["plugins"]
                    plugin_results = {}
                    
                    if isinstance(plugins_to_run, list):
                        for plugin_name in plugins_to_run:
                            if self.plugin_manager.has_plugin(plugin_name):
                                result = self.plugin_manager.execute_plugin(plugin_name, plugin_context)
                                if result:
                                    plugin_results[plugin_name] = result
                    
                    # Add plugin results to the response
                    if plugin_results:
                        processed_response["plugin_results"] = plugin_results
            
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