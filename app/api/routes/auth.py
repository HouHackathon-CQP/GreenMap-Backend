import logging
from fastapi import APIRouter, Depends, HTTPException
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
    user = await crud.get_user_by_email(db, email=credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
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
    # Chỉ đơn giản là in ra log
    logger.info(f"User {current_user.email} đã bấm đăng xuất.")
    
    return {"message": "Đăng xuất thành công"}