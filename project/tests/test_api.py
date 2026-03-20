from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_empty_image():
    #1. définir le payload d'entrée à tester
    #2. appeler l'entrypoint via le client test
    #3. assert sur la réponse.
    
    file_content = b"fake image content"
    # construction de la structure multipart de file
    # nom fichier, contenu, type de contenu 
    file = {"file": ("test.jpg", file_content, "image/jpeg")}
    response = client.post("/files/upload", files=file)
    
    assert response.status_code == 200
    assert "filename" in response.json()