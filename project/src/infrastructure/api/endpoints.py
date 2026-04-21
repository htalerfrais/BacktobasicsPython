from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from celery.result import AsyncResult

from src.app.services.file_service import FileService
from src.infrastructure.api.schemas import ImageUploadResponse, TaskResponse, TaskStatusResponse
from src.infrastructure.celery.tasks import process_image_task
from src.infrastructure.storage import S3Storage


router = APIRouter(prefix="/images", tags=["Image Processing"])


def get_file_service() -> FileService:
    return FileService(storage=S3Storage())


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_file(file: UploadFile = File(...),
                      service: FileService = Depends(get_file_service)):
    data = await file.read()
    image_metadata = service.save(data=data, key=f"inputs/{file.filename}")
    return image_metadata


@router.post("/process", response_model=TaskResponse)
async def process_image(file: UploadFile = File(...),
                        file_service: FileService = Depends(get_file_service)):
    data = await file.read()
    metadata = file_service.save(data=data, key=f"inputs/{file.filename}")

    task = process_image_task.delay(metadata.object_key, file.filename)
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
