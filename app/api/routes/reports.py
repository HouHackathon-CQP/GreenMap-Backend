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

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_admin, get_current_user # Giữ nguyên import
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


# --- SỬA PHẦN NÀY (GET) ---
@router.get("", response_model=List[schemas.ReportRead])
async def read_reports(
    status: Optional[models.ReportStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    # 1. Đổi từ get_current_admin -> get_current_user
    current_user: models.User = Depends(get_current_user),
):
    # 2. Thêm kiểm tra quyền: Chỉ ADMIN hoặc MANAGER được xem
    # Lưu ý: check kỹ xem trong models role lưu là "MANAGER" hay models.UserRole.MANAGER
    if current_user.role not in ["ADMIN", "MANAGER", models.UserRole.ADMIN, models.UserRole.MANAGER]:
         raise HTTPException(status_code=403, detail="Not authorized")

    return await crud.get_reports(db=db, status=status, skip=skip, limit=limit)


# --- SỬA PHẦN NÀY (PUT) ---
@router.put("/{report_id}/status", response_model=schemas.ReportRead)
async def approve_report(
    report_id: int,
    status_update: schemas.ReportUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 2. Thêm kiểm tra quyền: Chỉ ADMIN hoặc MANAGER được duyệt
    if current_user.role not in ["ADMIN", "MANAGER", models.UserRole.ADMIN, models.UserRole.MANAGER]:
         raise HTTPException(status_code=403, detail="Not authorized")

    report = await crud.update_report_status(db, report_id, status_update.status)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if status_update.status == models.ReportStatus.APPROVED:
        background_tasks.add_task(push_report_to_orion, report)

    return report