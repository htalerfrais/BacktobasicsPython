from abc import ABC, abstractmethod

from src.domain.models import ProcessedImage

class ImageProcessor(ABC):
    # contrat pour tout algorithme de traitement d'image dans notre app
    # cette classe va servir de support au strategy pattern.
    # -> le service ImageProcessorService dans l'app permettra d'instancier le bon ImageProcessor
    # -> dans infrastructure/ ; on implémentera les "strategy Algorithmes" (modèle de traitement d'image)
    #   qui pourront être utilisés par le service pour créer le bon ImageProcessor.
    
    @abstractmethod
    def process(self, image_bytes : bytes) -> bytes:
        pass
