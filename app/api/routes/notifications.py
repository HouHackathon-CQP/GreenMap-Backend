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

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from app import crud, models, schemas
from app.api.deps import get_current_admin, get_current_user_silent
from app.db.session import get_db
from app.services import push
from app.core.config import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=schemas.DeviceTokenRead, include_in_schema=False)
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


@router.delete("/register/{token}", include_in_schema=False)
async def unregister_device_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    success = await crud.deactivate_token(db, token)
    if not success:
        raise HTTPException(status_code=404, detail="Token không tồn tại")
    return {"message": "Đã hủy đăng ký token"}


@router.get("/tokens", response_model=list[schemas.DeviceTokenRead], include_in_schema=False)
async def list_tokens(
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_all_tokens(db)


@router.post("/send", include_in_schema=False)
async def send_push_notification(
    message: schemas.PushMessage,
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    tokens = await crud.get_active_tokens(db)
    token_values = [item.token for item in tokens if item.token]
    if not token_values:
        raise HTTPException(status_code=400, detail="Chưa có device token nào để gửi.")

    result = None
    error_msg = None
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
        error_msg = str(exc)
        
        # Save failed notification history
        await crud.create_notification_history(
            db=db,
            title=message.title,
            body=message.body,
            data=json.dumps(message.data) if message.data else None,
            notification_type="token",
            sent_count=0,
            failed_count=len(token_values),
            sent_by_user_id=current_user.id,
            status="failed",
            error_message=error_msg,
        )
        
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi push notification, kiểm tra cấu hình Firebase.",
        ) from exc

    invalid_tokens = result.get("invalid_tokens", [])
    await crud.deactivate_tokens_by_value(db, invalid_tokens)
    valid_ids = [item.id for item in tokens if item.token not in invalid_tokens]
    await crud.mark_tokens_sent(db, valid_ids)

    # Save notification history
    sent_count = result.get("success", 0)
    failed_count = result.get("failure", 0)
    status = "sent" if failed_count == 0 else ("partial" if sent_count > 0 else "failed")
    
    await crud.create_notification_history(
        db=db,
        title=message.title,
        body=message.body,
        data=json.dumps(message.data) if message.data else None,
        notification_type="token",
        sent_count=sent_count,
        failed_count=failed_count,
        sent_by_user_id=current_user.id,
        status=status,
        error_message=f"Invalid tokens: {len(invalid_tokens)}" if invalid_tokens else None,
    )

    return {
        "sent": result.get("success", 0),
        "failed": result.get("failure", 0),
        "invalid_tokens": invalid_tokens,
    }


@router.post("/send/topic", include_in_schema=False)
async def send_topic_notification(
    message: schemas.TopicPushMessage,
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Gửi thông báo tới một topic Firebase (mặc định lấy từ env FIREBASE_DEFAULT_TOPIC).
    Mobile app phải subscribe topic này.
    """
    topic = message.topic or settings.firebase_default_topic
    if not topic:
        raise HTTPException(status_code=400, detail="Chưa cấu hình topic mặc định.")

    result = None
    error_msg = None
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
        error_msg = str(exc)
        
        # Save failed notification history
        await crud.create_notification_history(
            db=db,
            title=message.title,
            body=message.body,
            data=json.dumps(message.data) if message.data else None,
            notification_type="topic",
            topic=topic,
            sent_count=0,
            failed_count=1,
            sent_by_user_id=current_user.id,
            status="failed",
            error_message=error_msg,
        )
        
        raise HTTPException(
            status_code=500,
            detail="Không thể gửi push notification theo topic, kiểm tra cấu hình Firebase.",
        ) from exc

    # Save notification history
    await crud.create_notification_history(
        db=db,
        title=message.title,
        body=message.body,
        data=json.dumps(message.data) if message.data else None,
        notification_type="topic",
        topic=topic,
        sent_count=1,
        failed_count=0,
        sent_by_user_id=current_user.id,
        status="sent",
    )

    return {"topic": topic, "message_id": result.get("message_id")}


@router.get("/history", response_model=schemas.NotificationHistoryList, include_in_schema=False)
async def get_notification_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Literal["token", "topic"] | None = Query(None, description="Filter by type: token, topic"),
    user_id: int | None = Query(None, description="Filter by target user ID"),
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách lịch sử thông báo đã gửi.
    Admin có thể xem tất cả hoặc filter theo type/user.
    """
    items, total = await crud.get_notification_history(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        notification_type=notification_type,
    )
    return schemas.NotificationHistoryList(total=total, items=items)


@router.get("/history/{notification_id}", response_model=schemas.NotificationHistoryRead, include_in_schema=False)
async def get_notification_by_id(
    notification_id: int,
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy chi tiết một bản ghi lịch sử thông báo.
    """
    notification = await crud.get_notification_history_by_id(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi lịch sử thông báo")
    return notification


@router.delete("/history/cleanup", include_in_schema=False)
async def cleanup_old_notifications(
    days: int = Query(90, ge=1, le=365, description="Xóa thông báo cũ hơn số ngày này"),
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa lịch sử thông báo cũ để dọn dẹp database.
    Mặc định xóa các bản ghi cũ hơn 90 ngày.
    """
    deleted_count = await crud.delete_old_notification_history(db, days)
    return {
        "message": f"Đã xóa {deleted_count} bản ghi lịch sử thông báo cũ hơn {days} ngày",
        "deleted_count": deleted_count,
    }
