from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.services.orion import push_report_to_orion

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=schemas.ReportRead)
async def create_new_report(
    report: schemas.ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud.create_report(db=db, report=report, user_id=current_user.id)


@router.get("", response_model=List[schemas.ReportRead])
async def read_reports(
    status: Optional[models.ReportStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    return await crud.get_reports(db=db, status=status, skip=skip, limit=limit)


@router.put("/{report_id}/status", response_model=schemas.ReportRead)
async def approve_report(
    report_id: int,
    status_update: schemas.ReportUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    report = await crud.update_report_status(db, report_id, status_update.status)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if status_update.status == models.ReportStatus.APPROVED:
        background_tasks.add_task(push_report_to_orion, report)

    return report
