from src.domain.interfaces import ImageProcessor
from src.utils.decorators import time_logger
from typing import List

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
    
    
class CompositeProcessor(ImageProcessor):
    def __init__(self, processors : List[ImageProcessor]):
        self._processors = processors
        
    @time_logger
    def process(self, image_bytes : bytes) -> bytes:
        output = image_bytes
        for processor in self._processors:
            output = processor.process(output)
        return output 

