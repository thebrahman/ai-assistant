import logging
import mss
import mss.tools
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ScreenshotCapture:
    """Handles capturing screenshots of the active window."""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.format = "png"
        self.quality = 85
        
        if config_manager:
            self.format = config_manager.get("screenshot", "format", default="png")
            self.quality = config_manager.get("screenshot", "quality", default=85)
    
    def capture_active_window(self):
        """
        Capture a screenshot of the active window.
        
        Returns:
            bytes: Image data as bytes
        """
        try:
            with mss.mss() as sct:
                # For the prototype, we'll just capture the main monitor
                # In a full implementation, you'd detect the active window
                monitor = sct.monitors[1]  # Main monitor
                
                # Capture the monitor
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image for processing
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Convert to bytes for API transmission
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=self.format.upper(), quality=self.quality)
                
                logger.info(f"Screenshot captured: {img.width}x{img.height}")
                return img_byte_arr.getvalue()
                
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def save_screenshot(self, path):
        """
        Capture a screenshot and save it to disk.
        
        Args:
            path (str): Path to save the screenshot
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            screenshot_data = self.capture_active_window()
            if screenshot_data:
                with open(path, 'wb') as f:
                    f.write(screenshot_data)
                logger.info(f"Screenshot saved to {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return False