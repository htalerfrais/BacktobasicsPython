from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from pathlib import Path
from celery.result import AsyncResult

from src.app.services.file_service import FileService
from src.infrastructure.api.schemas import ImageUploadResponse, TaskResponse, TaskStatusResponse
from src.infrastructure.celery.tasks import process_image_task


router = APIRouter(prefix="/images", tags=["Image Processing"])

# factory functions 
# instancier dépendances via Depends() de FastAPI.
def get_file_service() -> FileService:
    return FileService(upload_dir="uploads/images")


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_file(file: UploadFile = File(...),
                      service: FileService = Depends(get_file_service)):
    data = await file.read()
    image_metadata = service.save_file(data=data, filename=file.filename)
    return image_metadata


@router.post("/process", response_model=TaskResponse)
async def process_image(file: UploadFile = File(...),
                        file_service: FileService = Depends(get_file_service)):
    data = await file.read()
    # On sauvegarde d'abord le fichier dans le volume partagé api/worker !!!! IMPORTANT
    metadata = file_service.save_file(data=data, filename=file.filename)

    task = process_image_task.delay(metadata.path, file.filename)
    return TaskResponse(task_id=task.id, status="PENDING")


@router.get("/process/{task_id}", response_model=TaskStatusResponse)
async def get_process_status(task_id: str):
    task = AsyncResult(task_id)

    if task.failed():
        raise HTTPException(status_code=500, detail=str(task.result))

    result = None
    if task.successful():
        result = ImageUploadResponse(**task.result)

    return TaskStatusResponse(task_id=task_id, status=task.status, result=result)
