# ici on implémente le modèle Pydantic qui va servir de contrat à notre API d'upload d'image.
# ce modèle sera renvoyé par FastAPI

from pydantic import BaseModel, ConfigDict
from typing import Optional

# ici on est à l'extérieur du domaine donc on a le droit de connaître l'intérieur (le domain/model)
from src.domain.models import ImageMetadata

class ImageUploadResponse(BaseModel):
    file_id : Optional[int] = None
    path : str = None
    
    filename : str
    size_bytes : int
    file_extension : str
    
    # pour que ImageUploadResponse model puisse être généré à partir d'un objet au lieu d'un JSON
    # dans domain, le model dataclass de ImageMetadata va être généré,
    # puis à partir de celui ci on générera un model pydantic pour l'API.
    model_config = ConfigDict(from_attributes=True)


if __name__ == "__main__" : 
    image_metadata = ImageMetadata(filename="testblub.jpg", file_extension="jpg", size_bytes=3000)
    response = ImageUploadResponse.model_validate(image_metadata)
    print(response.model_dump())