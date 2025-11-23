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


