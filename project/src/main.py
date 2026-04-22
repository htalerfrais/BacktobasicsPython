from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from src.infrastructure.api.endpoints import router as file_router


app = FastAPI()
app.include_router(file_router)

# for prometheus metrics
Instrumentator().instrument(app).expose(app)
