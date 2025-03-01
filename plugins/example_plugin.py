from core.plugin_manager import Plugin

class ExamplePlugin(Plugin):
    """Example plugin that demonstrates the plugin architecture."""
    
    def initialize(self):
        """Initialize the plugin."""
        self.logger.info("Example plugin initialized")
    
    def execute(self, context):
        """
        Execute the plugin functionality.
        
        Args:
            context (dict): Context data for the plugin
            
        Returns:
            dict: Result of plugin execution
        """
        self.logger.info(f"Example plugin executed with context: {context}")
        
        # Just echo back the context with a message added
        return {
            "status": "success",
            "message": "Example plugin executed successfully",
            "input_context": context
        } 