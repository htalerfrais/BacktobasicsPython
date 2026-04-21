from abc import ABC, abstractmethod

from src.domain.models import ProcessedImage, ImageMetadata


class ImageProcessor(ABC):
    # contrat pour tout algorithme de traitement d'image dans notre app
    # cette classe va servir de support au strategy pattern.
    # -> le service ImageProcessorService dans l'app permettra d'instancier le bon ImageProcessor
    # -> dans infrastructure/ ; on implémentera les "strategy Algorithmes" (modèle de traitement d'image)
    #   qui pourront être utilisés par le service pour créer le bon ImageProcessor.

    @abstractmethod
    def process(self, image_bytes: bytes) -> ProcessedImage:
        pass


class StoragePort(ABC):
    # Contrat pour tout backend de stockage d'objets (MinIO, S3, disque local...).
    # Découple la couche app (FileService) des détails d'infrastructure boto3/filesystem.

    @abstractmethod
    def save(self, data: bytes, key: str) -> ImageMetadata:
        """Persiste `data` sous la clé `key` et retourne les métadonnées de l'objet stocké."""
        pass

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Retourne les octets de l'objet identifié par `key`."""
        pass
