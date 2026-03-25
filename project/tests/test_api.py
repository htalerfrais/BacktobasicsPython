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
    

def test_image_process():
    # test process d'une image par un DummyProcessor
    file_name = "lenna.jpg"
    file_content = b"fake binary data for image"
    files = {"file": (file_name, file_content, "image/jpeg")}
    
    response = client.post("/images/process", files=files)

    assert response.status_code == 200
    data = response.json()

    # nom du fichier retourné commence par "proc_" et contient file_name 
    assert data["filename"].startswith("proc_")
    assert file_name in data["filename"]

    # Nettoyage du fichier enregistré pour le test
    if os.path.exists(data["path"]):
        os.remove(data["path"])