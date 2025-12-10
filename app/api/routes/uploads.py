# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.core.config import settings

router = APIRouter(tags=["uploads"])

STATIC_IMAGES_DIR = Path(settings.static_dir) / "images"
STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", include_in_schema=False)
async def upload_image(file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = STATIC_IMAGES_DIR / file_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/images/{file_name}"}
