from src.domain.interfaces import StoragePort
from src.domain.models import ImageMetadata


class FileService:
    """Service applicatif de gestion des fichiers.
    
    Délègue entièrement au StoragePort injecté — ne connaît pas boto3 ni le filesystem.
    """

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def save(self, data: bytes, key: str) -> ImageMetadata:
        return self.storage.save(data, key)

    def get(self, key: str) -> bytes:
        return self.storage.get(key)
