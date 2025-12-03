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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_user, get_current_admin
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserRead])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách tất cả user (yêu cầu đăng nhập)"""
    return await crud.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lấy thông tin user theo ID (yêu cầu đăng nhập)"""
    db_user = await crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("", response_model=schemas.UserRead)
async def create_new_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Tạo user mới (không cần đăng nhập)"""
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật thông tin user (chỉ Admin hoặc chính user đó mới được cập nhật)"""
    # Check quyền: Admin hoặc chính user đó
    if current_user.role != models.UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Bạn chỉ có thể cập nhật thông tin của chính mình hoặc bạn cần quyền Admin",
        )
    
    db_user = await crud.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Xóa user (chỉ Admin mới có quyền)"""
    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.post("/change-password/me")
async def change_password(
    change_password_request: schemas.ChangePasswordRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Đổi mật khẩu của user hiện tại"""
    success = await crud.change_password(
        db,
        current_user.id,
        change_password_request.current_password,
        change_password_request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )
    
    return {"message": "Password changed successfully"}
