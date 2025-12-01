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

from fastapi import APIRouter, HTTPException, Query

from app import schemas
from app.services import rss

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/hanoimoi", response_model=list[schemas.NewsItem])
async def get_hanoimoi_news(
    limit: int = Query(20, ge=1, le=50, description="Số lượng bài viết tối đa trả về"),
):
    try:
        return await rss.fetch_hanoimoi_environment_news(limit=limit)
    except HTTPException:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Lỗi đọc RSS: {exc}") from exc


