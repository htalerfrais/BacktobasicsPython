from src.domain.interfaces import ImageProcessor

class DummyProcessor(ImageProcessor):
    def process(self, image_bytes : bytes) -> bytes : 
        print("using dummy processor pretending to process")
        return image_bytes
    
        
class WhiteProcessor(ImageProcessor):
    def process(self, image_bytes : bytes) -> bytes:
        print("using whiteprocessor")
        return image_bytes