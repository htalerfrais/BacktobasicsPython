from pathlib import Path

from src.infrastructure.celery.celery_app import app
from src.app.services.image_service import ImageProcessorService
from src.app.services.file_service import FileService
from src.infrastructure.processors import PyTorchBackgroundRemover

_service: ImageProcessorService | None = None

# pour ne pas charger le model dans le process Uvicorn.
# que dans les workers qui lient la tache et run _get_service().
def _get_service() -> ImageProcessorService:
    global _service # on instancie le service au niveau du module.
    if _service is None:
        processor = PyTorchBackgroundRemover(device="cpu")
        _service = ImageProcessorService(image_processor=processor)
    return _service


@app.task(bind=True)
def process_image_task(self, input_path: str, original_filename: str) -> dict:
    image_bytes = Path(input_path).read_bytes()

    result = _get_service().execute_processing(image_bytes)

    file_stem = Path(original_filename).stem
    output_filename = f"proc_{file_stem}.{result.file_extension}"

    file_service = FileService(upload_dir="uploads/images")
    metadata = file_service.save_file(data=result.data, filename=output_filename)

    return {
        "filename": metadata.filename,
        "path": metadata.path,
        "file_extension": metadata.file_extension,
        "size_bytes": metadata.size_bytes,
    }

