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
        
        suffix = Path(filename).suffix.lower()
        file_extension = suffix.lstrip(".")

        size_bytes = len(data)

        filepath = os.path.join(self.upload_dir, filename)

        image_metadata = ImageMetadata(
            filename=filename,
            file_extension=file_extension,
            size_bytes=size_bytes,
            path=filepath
        )
        
        with open(filepath, "wb") as f:
            f.write(data)
        
        return image_metadata