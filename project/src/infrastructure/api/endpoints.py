from fastapi import APIRouter

# tout comme on crée une instance de app dans main.py, 
# ici on crée un router
router = APIRouter(prefix="/files", tags=["images"])

@router.post("/upload")
async def upload_file(file):
    pass