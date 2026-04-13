from pathlib import Path

from src.infrastructure.celery.celery_app import app
from src.app.services.image_service import ImageProcessorService
from src.app.services.file_service import FileService
from src.infrastructure.processors import PyTorchBackgroundRemover


@app.task(bind=True)
def process_image_task(self, input_path: str, original_filename: str) -> dict:
    """
    Inbound adapter Celery — équivalent du endpoint HTTP pour le canal async.
    Responsabilités :
      1. Lire les bytes depuis le volume partagé (input_path)
      2. Déléguer au cas d'usage application (ImageProcessorService)
      3. Sauvegarder le résultat via FileService
      4. Retourner les métadonnées sérialisables pour le backend Redis
    """
    image_bytes = Path(input_path).read_bytes()

    # Couche application — le Singleton garantit que le modèle n'est chargé
    # qu'une seule fois par process worker, pas à chaque tâche.
    processor = PyTorchBackgroundRemover(device="cpu")
    service = ImageProcessorService(image_processor=processor)
    result = service.execute_processing(image_bytes)

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
