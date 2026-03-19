from fastapi import APIRouter, UploadFile, Depends, File
from src.app.services.file_service import FileService
from src.infrastructure.api.schemas import ImageUploadResponse

# tout comme on crée une instance de app dans main.py, 
# ici on crée un router
router = APIRouter(prefix="/files", tags=["images"])


# factory functions 
# instancier dépendances via Depends() de FastAPI.
def get_file_service() -> FileService:
    return FileService(upload_dir="uploads/images")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_file(file: UploadFile = File(...) , service : FileService = Depends(get_file_service)):
    data = await file.read() # lecture du fichier => bytes
    image_metadata = service.save_file(data=data, filename=file.filename)
    
    return image_metadata