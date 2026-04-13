from pathlib import Path
from unittest.mock import patch, MagicMock
from src.domain.models import ProcessedImage

from fastapi.testclient import TestClient
from src.main import app
import os

client = TestClient(app)

def test_empty_image():
    #1. définir le payload d'entrée à tester
    #2. appeler l'entrypoint via le client test
    #3. assert sur la réponse.
    
    file_content = b"fake image content"
    # construction de la structure multipart de file
    # nom fichier, contenu, type de contenu 
    file = {"file": ("test.jpg", file_content, "image/jpeg")}
    response = client.post("/images/upload", files=file)
    
    assert response.status_code == 200
    assert "filename" in response.json()
    

        

def test_image_process_mocked():
    # ce test mock la méthode d'execute_process, on ne test que l'endpoint, pas le service qui lui est patché.
    with patch("src.app.services.image_service.ImageProcessorService.execute_processing") as mock_exec :
        mock_exec.return_value = ProcessedImage(data=b"fake_output", file_extension="png")
        file_name = "lenna.jpg"
        files = {"file": ("lenna.jpg", b"fake_input", "image/jpeg")}
        response = client.post("/images/process", files=files)
        assert response.status_code == 200
        data = response.json()

        # nom du fichier retourné commence par "proc_" et contient file_name 
        assert data["filename"].startswith("proc_")
        stem = Path(file_name).stem
        assert data["filename"] == f"proc_{stem}.{data['file_extension']}"

        # Nettoyage du fichier enregistré pour le test
        if os.path.exists(data["path"]):
            os.remove(data["path"])
            
        mock_exec.assert_called_once()