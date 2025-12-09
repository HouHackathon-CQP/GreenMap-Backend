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

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_user_silent
from app.db.session import get_db
from app.services.ai_insights import generate_ai_insight


Provider = Literal["gemini", "groq", "auto"]
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/weather-insights", response_model=schemas.AIReportRead)
async def get_ai_weather_insights(
    lat: float = Query(21.0285, description="Vĩ độ (mặc định: Hà Nội)"),
    lon: float = Query(105.8542, description="Kinh độ (mặc định: Hà Nội)"),
    provider: Provider = Query("auto", description="Chọn provider AI: gemini, groq hoặc auto để thử lần lượt."),
    model: str | None = Query(
        None,
        description="Ghi đè model nếu cần (ví dụ: gemini-1.5-pro). Bỏ trống để dùng mặc định.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_silent),
):
    """
    Phân tích thời tiết 24h/7 ngày + AQI bằng AI (Gemini/Groq) và trả về lời khuyên.
    """
    try:
        ai_result = await generate_ai_insight(
            lat=lat,
            lon=lon,
            provider=provider,
            model_override=model,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    analysis_text = ai_result.get("analysis")
    if not analysis_text:
        raise HTTPException(status_code=502, detail="AI không trả về nội dung phân tích.")

    saved = await crud.create_ai_report(
        db=db,
        provider=ai_result.get("provider") or provider,
        model=ai_result.get("model"),
        lat=lat,
        lon=lon,
        analysis=analysis_text,
        context=ai_result.get("context"),
        user_id=current_user.id if current_user else None,
    )
    return saved


@router.get("/weather-insights/history", response_model=list[schemas.AIReportRead])
async def get_ai_weather_history(
    skip: int = Query(0, ge=0, description="Bỏ qua n kết quả đầu."),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa trả về."),
    db: AsyncSession = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_silent),
):
    """
    Xem lại các bản phân tích AI đã tạo. Nếu đăng nhập, chỉ trả về lịch sử của bạn.
    """
    user_id = current_user.id if current_user else None
    return await crud.list_ai_reports(db=db, user_id=user_id, skip=skip, limit=limit)
