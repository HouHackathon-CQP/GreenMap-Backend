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

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_admin, get_current_user_silent
from app.db.session import get_db
from app.services import push
from app.core.config import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=schemas.DeviceTokenRead)
async def register_device_token(
    payload: schemas.DeviceTokenCreate,
    current_user: models.User | None = Depends(get_current_user_silent),
    db: AsyncSession = Depends(get_db),
):
    """
    Lưu/ cập nhật Firebase device token cho mobile app.
    Cho phép gửi kèm Bearer token để gắn với user nếu có.
    """
    device = await crud.upsert_device_token(
        db,
        token=payload.token,
        platform=payload.platform,
        user=current_user,
    )
    return device


@router.delete("/register/{token}")
async def unregister_device_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    success = await crud.deactivate_token(db, token)
    if not success:
        raise HTTPException(status_code=404, detail="Token không tồn tại")
    return {"message": "Đã hủy đăng ký token"}


@router.get("/tokens", response_model=list[schemas.DeviceTokenRead])
async def list_tokens(
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_all_tokens(db)


@router.post("/send")
async def send_push_notification(
    message: schemas.PushMessage,
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    tokens = await crud.get_active_tokens(db)
    token_values = [item.token for item in tokens if item.token]
    if not token_values:
        raise HTTPException(status_code=400, detail="Chưa có device token nào để gửi.")

    try:
        result = await push.send_push_to_tokens(
            tokens=token_values,
            title=message.title,
            body=message.body,
            data=message.data,
            dry_run=message.dry_run,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Gửi push notification thất bại: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi push notification, kiểm tra cấu hình Firebase.",
        ) from exc

    invalid_tokens = result.get("invalid_tokens", [])
    await crud.deactivate_tokens_by_value(db, invalid_tokens)
    valid_ids = [item.id for item in tokens if item.token not in invalid_tokens]
    await crud.mark_tokens_sent(db, valid_ids)

    return {
        "sent": result.get("success", 0),
        "failed": result.get("failure", 0),
        "invalid_tokens": invalid_tokens,
    }


@router.post("/send/topic")
async def send_topic_notification(
    message: schemas.TopicPushMessage,
    current_user: models.User = Depends(get_current_admin),
):
    """
    Gửi thông báo tới một topic Firebase (mặc định lấy từ env FIREBASE_DEFAULT_TOPIC).
    Mobile app phải subscribe topic này.
    """
    topic = message.topic or settings.firebase_default_topic
    if not topic:
        raise HTTPException(status_code=400, detail="Chưa cấu hình topic mặc định.")

    try:
        result = await push.send_topic_notification(
            topic=topic,
            title=message.title,
            body=message.body,
            data=message.data,
            dry_run=message.dry_run,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Gửi push topic thất bại: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi push notification theo topic, kiểm tra cấu hình Firebase.",
        ) from exc

    return {"topic": topic, "message_id": result.get("message_id")}
