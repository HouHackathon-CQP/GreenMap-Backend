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

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_user, get_current_active_user
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserRead])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách user (Chỉ Admin và Manager được xem)"""
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Không đủ quyền truy cập danh sách người dùng")
        
    return await crud.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lấy thông tin user theo ID"""
    # Ai cũng xem được chi tiết (hoặc bạn có thể giới hạn lại nếu muốn)
    db_user = await crud.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("", response_model=schemas.UserRead)
async def create_new_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
    # Cho phép user là None (trường hợp đăng ký mới)
    current_user: Optional[models.User] = Depends(get_current_user), 
):
    """
    Tạo user mới.
    - Nếu không đăng nhập: Mặc định là CITIZEN.
    - Nếu là Manager: Chỉ được tạo CITIZEN.
    - Nếu là Admin: Tạo được mọi quyền.
    """
    # 1. Kiểm tra Email trùng
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Logic phân quyền khi tạo
    requested_role = user.role if hasattr(user, "role") else models.UserRole.CITIZEN

    # Nếu người tạo là Manager, không được phép tạo Admin hoặc Manager
    if current_user and current_user.role == models.UserRole.MANAGER:
        if requested_role in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
             raise HTTPException(status_code=403, detail="Manager chỉ được phép tạo tài khoản Công dân")
    
    # Nếu người dùng chưa đăng nhập (đăng ký public), bắt buộc là Citizen
    if not current_user:
        if requested_role != models.UserRole.CITIZEN:
             # Force về Citizen hoặc báo lỗi, ở đây ta gán cứng cho an toàn
             user.role = models.UserRole.CITIZEN

    return await crud.create_user(db=db, user=user)


@router.put("/{user_id}", response_model=schemas.UserRead)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cập nhật user.
    - Admin: Full quyền.
    - Manager: Chỉ sửa được Citizen (Không sửa được Admin/Manager khác).
    - Chính chủ: Sửa được bản thân.
    """
    # 1. Tìm user cần sửa
    target_user = await crud.get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check quyền
    is_admin = current_user.role == models.UserRole.ADMIN
    is_manager = current_user.role == models.UserRole.MANAGER
    is_self = current_user.id == user_id
    target_is_citizen = target_user.role == models.UserRole.CITIZEN

    # Logic chặn
    if is_self:
        pass # OK, được sửa chính mình
    elif is_admin:
        pass # OK, Admin quyền to nhất
    elif is_manager:
        # Manager chỉ được sửa nếu mục tiêu là Citizen
        if not target_is_citizen:
            raise HTTPException(status_code=403, detail="Manager không thể chỉnh sửa Admin hoặc Manager khác")
    else:
        # User thường không được sửa người khác
        raise HTTPException(status_code=403, detail="Không đủ quyền thực hiện")
    
    # 3. Thực hiện update
    updated_user = await crud.update_user(db, user_id, user_update)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    # QUAN TRỌNG: Đổi get_current_admin thành get_current_active_user để Manager vào được hàm
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa user.
    - Admin: Xóa tất cả.
    - Manager: Chỉ xóa được Citizen.
    """
    # 1. Tìm user cần xóa để check role của nó
    target_user = await crud.get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check quyền
    is_admin = current_user.role == models.UserRole.ADMIN
    is_manager = current_user.role == models.UserRole.MANAGER
    target_is_citizen = target_user.role == models.UserRole.CITIZEN

    if is_admin:
        pass # Admin xóa ai cũng được
    elif is_manager:
        # Manager xóa ai cũng được TRỪ Admin và Manager khác
        if not target_is_citizen:
             raise HTTPException(status_code=403, detail="Manager không thể xóa Admin hoặc Manager khác")
    else:
        # Citizen không có quyền xóa
        raise HTTPException(status_code=403, detail="Không đủ quyền thực hiện")

    # 3. Thực hiện xóa
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
    result = await crud.change_password(
        db,
        current_user.id,
        change_password_request.current_password,
        change_password_request.new_password,
    )
    
    if result == "user_not_found":
        raise HTTPException(status_code=404, detail="User not found")
    elif result == "incorrect_password":
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
    elif result != "success":
        raise HTTPException(status_code=500, detail="Unknown error")
    
    return {"message": "Password changed successfully"}