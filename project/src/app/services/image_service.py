from src.domain.interfaces import ImageProcessor
from src.infrastructure.processors import DummyProcessor, WhiteProcessor

class ImageProcessorService():
    def __init__(self, image_processor : ImageProcessor):
        self.image_processor = image_processor
        

if __name__ == "__main__":
    # sélectionner la stratégie (aller chercher dans les infrastructures) 
    chosen_processor = DummyProcessor()
    # instanciation du service (app) qui utilise cette "stratégie algorithm" dont la classe parent est ABC dans domain
    ips = ImageProcessorService(chosen_processor)
    # run le service sur des bytes d'image.
    ips.image_processor.process(image_bytes = b"abraham")
    