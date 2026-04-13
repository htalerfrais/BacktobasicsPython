# ici on implémente le modèle Pydantic qui va servir de contrat à notre API d'upload d'image.
# ce modèle sera renvoyé par FastAPI

from pydantic import BaseModel, ConfigDict
from typing import Optional

from src.domain.models import ImageMetadata

class ImageUploadResponse(BaseModel):
    file_id : Optional[int] = None
    path : str = None
    
    filename : str
    size_bytes : int
    file_extension : str
    
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    """Retourné immédiatement par POST /process — la tâche est en file d'attente."""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Retourné par GET /process/{task_id} — inclut le résultat quand disponible."""
    task_id: str
    status: str
    result: Optional[ImageUploadResponse] = None


if __name__ == "__main__" : 
    image_metadata = ImageMetadata(filename="testblub.jpg", file_extension="jpg", size_bytes=3000)
    response = ImageUploadResponse.model_validate(image_metadata)
    print(response.model_dump())