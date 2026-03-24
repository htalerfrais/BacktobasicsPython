# this file is defining my usecase : orchestrating domain stuff
# il appel : le domaine et les infras. Il se fait appeler par: les infra. 

from src.domain.models import ImageMetadata
from pathlib import Path
import os

class FileService():
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        
    def save_file(self, data: bytes, filename: str) -> ImageMetadata:
        # 1. créer tous les champs / attributs nécéssaires à crer objet ImageMetadata
        # 2. sauver le fichier sur le disque.
        
        ext = Path(filename).suffix.lower()
        match ext:
            case ".jpeg" | ".jpg" | ".png":
                content_type = "image"
            case "pdf":
                content_type = "pdf"
        
        size_bytes = len(data)
        
        image_metadata = ImageMetadata(
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes
        )
        
        filepath = os.path.join(self.upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        
        return image_metadata