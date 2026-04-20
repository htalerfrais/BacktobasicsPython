from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from src.main import app
from src.domain.models import ImageMetadata

client = TestClient(app)


def test_empty_image():
    file = {"file": ("test.jpg", b"fake image content", "image/jpeg")}
    response = client.post("/images/upload", files=file)
    assert response.status_code == 200
    assert "filename" in response.json()


def test_process_enqueues_task():
    """POST /images/process doit déléguer à Celery et retourner task_id + status PENDING."""
    fake_metadata = ImageMetadata(
        filename="lenna.jpg",
        file_extension="jpg",
        size_bytes=100,
        path="uploads/images/lenna.jpg",
    )
    fake_task = MagicMock()
    fake_task.id = "fake-task-id-123"

    with patch("src.app.services.file_service.FileService.save_file", return_value=fake_metadata), \
         patch("src.infrastructure.api.endpoints.process_image_task") as mock_task:

        mock_task.delay.return_value = fake_task
        response = client.post("/images/process", files={"file": ("lenna.jpg", b"fake_input", "image/jpeg")})

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
    # Ce dict correspond exactement au return de process_image_task dans tasks.py
    fake_result = {
        "filename": "proc_lenna.png",
        "path": "uploads/images/proc_lenna.png",
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