from src.domain.interfaces import ImageProcessor
from src.utils.decorators import time_logger

class DummyProcessor(ImageProcessor):
    @time_logger
    def process(self, image_bytes : bytes) -> bytes : 
        print("using dummy processor pretending to process")
        return image_bytes
    
        
class WhiteProcessor(ImageProcessor):
    @time_logger
    def process(self, image_bytes : bytes) -> bytes:
        print("using whiteprocessor")
        return image_bytes