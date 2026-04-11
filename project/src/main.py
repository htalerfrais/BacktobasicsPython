from fastapi import FastAPI
from src.infrastructure.api.endpoints import router as file_router
from src.infrastructure.processors import PyTorchBackgroundRemover
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # instancier le Singleton => RAM attribuée à l'instance unique sur laquelle ça va pointer des qu'on rappelera le constructeur
    print("Chargement model")
    _ = PyTorchBackgroundRemover(device="cpu") 
    print("Modèle chargé.")
    
    yield # met la fonction en "pause" jusqu'à la fermeture de l'app FastAPI
    
    print("Arrêt de l'application.")


app = FastAPI(lifespan=lifespan)
app.include_router(file_router)


