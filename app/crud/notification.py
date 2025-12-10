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

from typing import Iterable

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def upsert_device_token(
    db: AsyncSession,
    token: str,
    platform: str | None = None,
    user: models.User | None = None,
) -> models.NotificationToken:
    result = await db.execute(
        select(models.NotificationToken).where(models.NotificationToken.token == token)
    )
    device = result.scalar_one_or_none()

    if device:
        device.platform = platform or device.platform
        device.is_active = True
        if user and device.user_id != user.id:
            device.user_id = user.id
    else:
        device = models.NotificationToken(
            token=token,
            platform=platform,
            user_id=user.id if user else None,
            is_active=True,
        )
        db.add(device)

    await db.commit()
    await db.refresh(device)
    return device


async def deactivate_token(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        select(models.NotificationToken).where(models.NotificationToken.token == token)
    )
    device = result.scalar_one_or_none()
    if not device:
        return False
    device.is_active = False
    await db.commit()
    return True


async def deactivate_tokens_by_value(db: AsyncSession, tokens: list[str]) -> int:
    if not tokens:
        return 0
    result = await db.execute(
        update(models.NotificationToken)
        .where(models.NotificationToken.token.in_(tokens))
        .values(is_active=False)
    )
    await db.commit()
    return result.rowcount or 0


async def get_active_tokens(db: AsyncSession) -> list[models.NotificationToken]:
    result = await db.execute(
        select(models.NotificationToken).where(models.NotificationToken.is_active.is_(True))
    )
    return result.scalars().all()


async def get_all_tokens(db: AsyncSession) -> list[models.NotificationToken]:
    result = await db.execute(
        select(models.NotificationToken).order_by(models.NotificationToken.created_at.desc())
    )
    return result.scalars().all()


async def mark_tokens_sent(db: AsyncSession, token_ids: Iterable[int]) -> None:
    ids = list(token_ids)
    if not ids:
        return
    await db.execute(
        update(models.NotificationToken)
        .where(models.NotificationToken.id.in_(ids))
        .values(last_sent_at=func.now())
    )
    await db.commit()


async def create_notification_history(
    db: AsyncSession,
    title: str,
    body: str,
    notification_type: str,
    sent_count: int = 0,
    failed_count: int = 0,
    data: str | None = None,
    topic: str | None = None,
    target_user_id: int | None = None,
    sent_by_user_id: int | None = None,
    status: str = "sent",
    error_message: str | None = None,
) -> models.NotificationHistory:
    """
    Tạo bản ghi lịch sử thông báo
    """
    history = models.NotificationHistory(
        title=title,
        body=body,
        data=data,
        notification_type=notification_type,
        topic=topic,
        target_user_id=target_user_id,
        sent_count=sent_count,
        failed_count=failed_count,
        sent_by_user_id=sent_by_user_id,
        status=status,
        error_message=error_message,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_notification_history(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    notification_type: str | None = None,
) -> tuple[list[models.NotificationHistory], int]:
    """
    Lấy danh sách lịch sử thông báo với phân trang và filter
    """
    query = select(models.NotificationHistory)
    
    if user_id:
        query = query.where(models.NotificationHistory.target_user_id == user_id)
    
    if notification_type:
        query = query.where(models.NotificationHistory.notification_type == notification_type)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(models.NotificationHistory.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return list(items), total


async def get_notification_history_by_id(
    db: AsyncSession,
    notification_id: int,
) -> models.NotificationHistory | None:
    """
    Lấy chi tiết lịch sử thông báo theo ID
    """
    result = await db.execute(
        select(models.NotificationHistory).where(models.NotificationHistory.id == notification_id)
    )
    return result.scalar_one_or_none()


async def delete_old_notification_history(
    db: AsyncSession,
    days: int = 90,
) -> int:
    """
    Xóa lịch sử thông báo cũ hơn số ngày chỉ định
    """
    from datetime import timedelta
    cutoff_date = func.now() - timedelta(days=days)
    
    result = await db.execute(
        select(models.NotificationHistory).where(
            models.NotificationHistory.created_at < cutoff_date
        )
    )
    old_records = result.scalars().all()
    
    for record in old_records:
        await db.delete(record)
    
    await db.commit()
    return len(old_records)
