# this file is defining my usecase : orchestrating domain stuff
# il appel : le domaine et les infras. Il se fait appeler par: les infra. 

from src.domain.models import ImageMetadata
from pathlib import Path


class FileService():
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
    def save_file(self, data: bytes, filename: str) -> ImageMetadata:
        path_obj = Path(filename)
        file_extension = path_obj.suffix.lower().lstrip(".")

        size_bytes = len(data)

        filepath = self.upload_dir / filename

        image_metadata = ImageMetadata(
            filename=path_obj.name,
            file_extension=file_extension,
            size_bytes=size_bytes,
            path=str(filepath)
        )
        
        # Utilisation de pathlib pour écrire directement (plus concis que open())
        filepath.write_bytes(data)
        
        return image_metadata