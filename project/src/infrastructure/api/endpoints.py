from fastapi import APIRouter, UploadFile, Depends, File
from src.app.services.file_service import FileService
from src.app.services.image_service import ImageProcessorService
from src.infrastructure.processors import DummyProcessor, WhiteProcessor, CompositeProcessor, PyTorchBackgroundRemover
from src.infrastructure.api.schemas import ImageUploadResponse

# tout comme on crée une instance de app dans main.py, 
# ici on crée un router
router = APIRouter(prefix="/images", tags=["Image Processing"])

# factory functions 
# instancier dépendances via Depends() de FastAPI.
def get_file_service() -> FileService:
    return FileService(upload_dir="uploads/images")

def get_image_processor_service() -> ImageProcessorService:
    # plus tard c'est ici qu'on mettra des conditions pour sélectionner quel processor on veut activer.
    processor = PyTorchBackgroundRemover()
    return ImageProcessorService(image_processor=processor)



@router.post("/upload", response_model=ImageUploadResponse)
async def upload_file(file: UploadFile = File(...) , 
                      service : FileService = Depends(get_file_service)):
    data = await file.read() # lecture du fichier => bytes
    image_metadata = service.save_file(data=data, filename=file.filename)
    
    return image_metadata


@router.post("/process", response_model = ImageUploadResponse)
async def process_image(file: UploadFile = File(...) , 
                        process_service : ImageProcessorService = Depends(get_image_processor_service) , 
                        file_service : FileService = Depends(get_file_service)
                        ):
    data = await file.read() # lecture
    processed_data = process_service.execute_processing(data) # Traitement de l'image
    image_metadata = file_service.save_file(data=processed_data, filename=f"proc_{file.filename}") # sauvegarde
    
    return image_metadata