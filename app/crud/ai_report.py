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

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models


async def create_ai_report(
    db: AsyncSession,
    *,
    provider: str,
    model: str | None,
    lat: float,
    lon: float,
    analysis: str,
    context: dict[str, Any] | None,
    user_id: int | None,
) -> models.AIReport:
    db_obj = models.AIReport(
        provider=provider,
        model=model,
        lat=lat,
        lon=lon,
        analysis=analysis,
        context=context,
        user_id=user_id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def list_ai_reports(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[models.AIReport]:
    query = select(models.AIReport).order_by(desc(models.AIReport.created_at))
    if user_id is not None:
        query = query.where(models.AIReport.user_id == user_id)
    else:
        query = query.where(models.AIReport.user_id.is_(None))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_ai_report(
    db: AsyncSession,
    report_id: int,
) -> models.AIReport | None:
    result = await db.execute(select(models.AIReport).where(models.AIReport.id == report_id))
    return result.scalar_one_or_none()
