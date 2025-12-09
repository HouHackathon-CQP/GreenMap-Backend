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
