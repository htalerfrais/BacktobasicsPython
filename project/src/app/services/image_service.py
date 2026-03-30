from src.domain.interfaces import ImageProcessor, ProcessedImage
from src.infrastructure.processors import DummyProcessor

class ImageProcessorService():
    def __init__(self, image_processor : ImageProcessor):
        self.image_processor = image_processor # can be a CompositeProcessor (so multiple ones)
        
    def execute_processing(self, image_bytes : bytes) -> ProcessedImage:
        return self.image_processor.process(image_bytes)
        

if __name__ == "__main__":
    # sélectionner la stratégie (aller chercher dans les infrastructures) 
    processor = DummyProcessor()
    # instanciation du service (app) qui utilise cette "stratégie algorithm" dont la classe parent est ABC dans domain
    ips = ImageProcessorService(processor)
    # run le service sur des bytes d'image.
    ips.execute_processing(image_bytes = b"abraham")
    