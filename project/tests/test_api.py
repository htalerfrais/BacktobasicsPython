from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from src.main import app
from src.app.services.file_service import FileService
from src.infrastructure.api.endpoints import get_file_service
from src.domain.models import ImageMetadata

client = TestClient(app)


def _fake_file_service(metadata: ImageMetadata) -> FileService:
    """FileService avec storage mocké — ne touche pas S3/MinIO."""
    mock_storage = MagicMock()
    mock_storage.save.return_value = metadata
    return FileService(storage=mock_storage)


def test_empty_image():
    fake_metadata = ImageMetadata(
        filename="test.jpg",
        file_extension="jpg",
        size_bytes=18,
        object_key="inputs/test.jpg",
    )
    # dependency_overrides : mécanisme natif FastAPI pour remplacer une dépendance en test
    app.dependency_overrides[get_file_service] = lambda: _fake_file_service(fake_metadata)
    try:
        response = client.post("/images/upload", files={"file": ("test.jpg", b"fake image content", "image/jpeg")})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "filename" in response.json()


def test_process_enqueues_task():
    """POST /images/process doit déléguer à Celery et retourner task_id + status PENDING."""
    fake_metadata = ImageMetadata(
        filename="lenna.jpg",
        file_extension="jpg",
        size_bytes=100,
        object_key="inputs/lenna.jpg",
    )
    fake_task = MagicMock()
    fake_task.id = "fake-task-id-123"

    app.dependency_overrides[get_file_service] = lambda: _fake_file_service(fake_metadata)
    try:
        with patch("src.infrastructure.api.endpoints.process_image_task") as mock_task:
            mock_task.delay.return_value = fake_task
            response = client.post("/images/process", files={"file": ("lenna.jpg", b"fake_input", "image/jpeg")})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "fake-task-id-123"
    assert data["status"] == "PENDING"
    mock_task.delay.assert_called_once()


def test_get_status_pending():
    """GET /images/process/{task_id} retourne PENDING et result null si la tâche n'est pas terminée."""
    mock_async = MagicMock()
    mock_async.status = "PENDING"
    mock_async.successful.return_value = False
    mock_async.failed.return_value = False

    with patch("src.infrastructure.api.endpoints.AsyncResult", return_value=mock_async):
        response = client.get("/images/process/fake-task-id-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["result"] is None


def test_get_status_success():
    """GET /images/process/{task_id} retourne le résultat complet quand la tâche est SUCCESS."""
    fake_result = {
        "filename": "proc_lenna.png",
        "object_key": "outputs/proc_lenna.png",
        "file_extension": "png",
        "size_bytes": 2048,
    }
    mock_async = MagicMock()
    mock_async.status = "SUCCESS"
    mock_async.successful.return_value = True
    mock_async.failed.return_value = False
    mock_async.result = fake_result

    with patch("src.infrastructure.api.endpoints.AsyncResult", return_value=mock_async):
        response = client.get("/images/process/fake-task-id-123")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["result"]["filename"] == "proc_lenna.png"
    assert data["result"]["file_extension"] == "png"
