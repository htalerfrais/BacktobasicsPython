# ici on implémente le modèle Pydantic qui va servir de contrat à notre API d'upload d'image.
# ce modèle sera renvoyé par FastAPI

from pydantic import BaseModel, ConfigDict
from typing import Optional

from src.domain.models import ImageMetadata

class ImageUploadResponse(BaseModel):
    """Retourné par POST /upload ou par GET /process/{task_id} si SUCCESS"""
    file_id : Optional[int] = None
    object_key: str
    filename : str
    size_bytes : int
    file_extension : str
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Retourné immédiatement par POST /process"""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Retourné par GET /process/{task_id}"""
    task_id: str
    status: str
    result: Optional[ImageUploadResponse] = None


if __name__ == "__main__" : 
    image_metadata = ImageMetadata(filename="testblub.jpg", file_extension="jpg", size_bytes=3000)
    response = ImageUploadResponse.model_validate(image_metadata)
    print(response.model_dump())