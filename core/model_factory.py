import logging
from core.gemini_connector import GeminiConnector
from core.openai_connector import OpenAIConnector

logger = logging.getLogger(__name__)

class ModelFactory:
    """Factory class to create appropriate model connectors."""
    
    @staticmethod
    def create_connector(config_manager):
        """
        Create the appropriate model connector based on configuration.
        
        Args:
            config_manager: The configuration manager instance
            
        Returns:
            ModelConnector: An instance of the appropriate model connector
            
        Raises:
            ValueError: If the specified model provider is not supported
        """
        default_provider = config_manager.get("models", "default", "gemini")
        
        # Check if the specified provider is enabled
        provider_enabled = config_manager.get(
            "models", "providers", default_provider, "enabled", True
        )
        
        if not provider_enabled:
            # If the default provider is disabled, try to find an enabled one
            providers = config_manager.get("models", "providers", {})
            for provider_name, provider_config in providers.items():
                if provider_config.get("enabled", False):
                    logger.warning(
                        f"Default provider '{default_provider}' is disabled. "
                        f"Using '{provider_name}' instead."
                    )
                    default_provider = provider_name
                    break
        
        # Create the appropriate connector
        if default_provider == "gemini":
            return GeminiConnector(config_manager)
        elif default_provider == "openai":
            return OpenAIConnector(config_manager)
        else:
            error_msg = f"Unsupported model provider: {default_provider}"
            logger.error(error_msg)
            raise ValueError(error_msg) 