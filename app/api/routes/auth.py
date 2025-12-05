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
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.api import deps
from app import models

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/login", response_model=schemas.TokenResponse)
async def login_for_access_token(
    credentials: schemas.LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Login attempt for: %s", credentials.email)
    
    # 1. Tìm User theo Email
    user = await crud.get_user_by_email(db, email=credentials.email)
    
    # 2. Kiểm tra Email có tồn tại không
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email không tồn tại trong hệ thống."
        )

    # 3. Kiểm tra Mật khẩu
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu không chính xác."
        )

    # 4. Kiểm tra Trạng thái tài khoản
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đã bị khóa. Vui lòng liên hệ Admin."
        )

    # 5. Tạo Token nếu mọi thứ OK
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }

@router.post("/logout")
async def logout(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    API Đăng xuất (Dùng để ghi log hành động).
    Frontend cần xóa token ở client sau khi gọi API này.
    """
    logger.info(f"User {current_user.email} đã bấm đăng xuất.")
    return {"message": "Đăng xuất thành công"}