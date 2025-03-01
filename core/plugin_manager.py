import os
import logging
import importlib
import inspect
from abc import ABC, abstractmethod

class Plugin(ABC):
    """Base class for plugins."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
    
    @abstractmethod
    def initialize(self):
        """Initialize the plugin. Called when the plugin is loaded."""
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    def execute(self, context):
        """
        Execute the plugin with the given context.
        
        Args:
            context (dict): Context data for the plugin
            
        Returns:
            Any: Result of the plugin execution
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    @property
    def name(self):
        """Get the plugin name (class name by default)."""
        return self.__class__.__name__
    
    @property
    def description(self):
        """Get the plugin description (docstring by default)."""
        return self.__doc__ or "No description available"


class PluginManager:
    """Manages loading and running plugins."""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.plugins = {}
        self.logger = logging.getLogger(__name__)
        self.plugin_dir = config_manager.get("plugins", "directory", "plugins")
        
        # Try to load plugins if enabled
        if config_manager.get("plugins", "enabled", False):
            self.load_plugins()
    
    def load_plugins(self):
        """Load all enabled plugins."""
        enabled_plugins = self.config_manager.get("plugins", "enabled_plugins", [])
        
        if not enabled_plugins:
            self.logger.info("No plugins enabled in configuration")
            return
        
        # Create the plugin directory if it doesn't exist
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            self.logger.info(f"Created plugin directory: {self.plugin_dir}")
            return  # No plugins to load yet
        
        # Ensure the plugins directory is importable as a package
        init_file = os.path.join(self.plugin_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write("# Plugin package initialization\n")
        
        # Add the current directory to sys.path if needed
        import sys
        if "" not in sys.path:
            sys.path.insert(0, "")
        
        # Load each enabled plugin
        for plugin_name in enabled_plugins:
            try:
                # Import the plugin module
                module_path = f"{self.plugin_dir}.{plugin_name}"
                module = importlib.import_module(module_path)
                
                # Find all Plugin subclasses in the module
                plugin_classes = []
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Plugin) and 
                        obj != Plugin):
                        plugin_classes.append(obj)
                
                if not plugin_classes:
                    self.logger.warning(f"No Plugin subclasses found in {plugin_name}")
                    continue
                
                # Initialize each plugin class found
                for plugin_class in plugin_classes:
                    try:
                        plugin_instance = plugin_class(self.config_manager)
                        plugin_instance.initialize()
                        self.plugins[plugin_instance.name] = plugin_instance
                        self.logger.info(f"Loaded plugin: {plugin_instance.name}")
                    except Exception as e:
                        self.logger.error(f"Error initializing plugin {plugin_class.__name__}: {e}")
                
            except Exception as e:
                self.logger.error(f"Error loading plugin module {plugin_name}: {e}")
    
    def execute_plugin(self, plugin_name, context):
        """
        Execute a specific plugin.
        
        Args:
            plugin_name (str): Name of the plugin to execute
            context (dict): Context data for the plugin
            
        Returns:
            Any: Result of the plugin execution or None if plugin not found
        """
        if plugin_name in self.plugins:
            try:
                self.logger.info(f"Executing plugin: {plugin_name}")
                return self.plugins[plugin_name].execute(context)
            except Exception as e:
                self.logger.error(f"Error executing plugin {plugin_name}: {e}")
                return None
        else:
            self.logger.warning(f"Plugin not found: {plugin_name}")
            return None
    
    def get_available_plugins(self):
        """
        Get a list of available plugins.
        
        Returns:
            list: List of dictionaries with plugin info
        """
        plugin_info = []
        for name, plugin in self.plugins.items():
            plugin_info.append({
                "name": name,
                "description": plugin.description
            })
        return plugin_info
    
    def has_plugin(self, plugin_name):
        """Check if a plugin is available."""
        return plugin_name in self.plugins 