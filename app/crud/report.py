from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReportStatus, UserReport
from app.schemas import ReportCreate


async def create_report(db: AsyncSession, report: ReportCreate, user_id: int) -> UserReport:
    db_report = UserReport(
        **report.model_dump(),
        user_id=user_id,
        status=ReportStatus.PENDING,
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


async def get_reports(
    db: AsyncSession,
    status: Optional[ReportStatus] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(UserReport)
    if status:
        query = query.where(UserReport.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_report_status(
    db: AsyncSession, report_id: int, status: ReportStatus
) -> UserReport | None:
    result = await db.execute(select(UserReport).where(UserReport.id == report_id))
    db_report = result.scalar_one_or_none()
    if not db_report:
        return None
    db_report.status = status
    await db.commit()
    await db.refresh(db_report)
    return db_report
