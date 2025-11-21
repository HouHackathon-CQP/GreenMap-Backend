import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas
import crud
import config
from database import SessionLocal, engine, Base
from models import UserRole

async def init_models():
    """Tạo bảng nếu chưa có"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_super_user(db: AsyncSession):
    """Tạo tài khoản Admin đầu tiên"""
    email = config.FIRST_SUPERUSER
    password = config.FIRST_SUPERUSER_PASSWORD
    
    # 1. Kiểm tra xem admin đã tồn tại chưa
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    
    if user:
        print(f"--- Admin user {email} đã tồn tại. Bỏ qua. ---")
    else:
        print(f"--- Đang tạo Admin user: {email} ---")
        # Tạo Schema dữ liệu
        user_in = schemas.UserCreate(
            email=email,
            password=password,
            full_name="Super Admin"
        )
        # Gọi CRUD nhưng ÉP BUỘC role là ADMIN
        await crud.create_user(db, user_in, role=UserRole.ADMIN)
        print("--- Tạo Admin thành công! ---")

async def main():
    print("--- Bắt đầu khởi tạo hệ thống ---")
    await init_models() # Tạo bảng
    
    async with SessionLocal() as db:
        await create_super_user(db)
        
    print("--- Hoàn tất khởi tạo ---")

if __name__ == "__main__":
    asyncio.run(main())