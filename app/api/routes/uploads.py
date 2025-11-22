import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.config import settings

router = APIRouter(tags=["uploads"])

STATIC_IMAGES_DIR = Path(settings.static_dir) / "images"
STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = STATIC_IMAGES_DIR / file_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/images/{file_name}"}
