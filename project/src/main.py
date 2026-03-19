from fastapi import FastAPI
from src.infrastructure.api.endpoints import router as file_router

app = FastAPI()
app.include_router(file_router)


