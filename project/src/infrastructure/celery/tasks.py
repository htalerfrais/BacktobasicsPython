from pathlib import Path

from src.infrastructure.celery.celery_app import app
from src.app.services.image_service import ImageProcessorService
from src.app.services.file_service import FileService
from src.infrastructure.processors import PyTorchBackgroundRemover
from src.infrastructure.storage import S3Storage

_service: ImageProcessorService | None = None

# pour ne pas charger le model dans le process Uvicorn.
# que dans les workers qui lient la tache et run _get_service().
# pour ne pas charger le model dans le process Uvicorn.
# que dans les workers qui lient la tache et run _get_service().
def _get_service() -> ImageProcessorService:
    global _service
    if _service is None:
        processor = PyTorchBackgroundRemover(device="cpu")
        _service = ImageProcessorService(image_processor=processor)
    return _service


@app.task(bind=True)
def process_image_task(self, input_key: str, original_filename: str) -> dict:
    file_service = FileService(storage=S3Storage())

    image_bytes = file_service.get(input_key)

    result = _get_service().execute_processing(image_bytes)

    file_stem = Path(original_filename).stem
    output_key = f"outputs/proc_{file_stem}.{result.file_extension}"
    metadata = file_service.save(data=result.data, key=output_key)

    return {
        "filename": metadata.filename,
        "object_key": metadata.object_key,
        "file_extension": metadata.file_extension,
        "size_bytes": metadata.size_bytes,
    }

