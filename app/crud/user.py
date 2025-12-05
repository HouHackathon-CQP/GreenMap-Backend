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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import User, UserRole
from app.schemas import UserCreate, UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def create_user(
    db: AsyncSession, user: UserCreate, role: UserRole = UserRole.CITIZEN
) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(
    db: AsyncSession, user_id: int, user_update: UserUpdate
) -> User | None:
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    await db.delete(db_user)
    await db.commit()
    return True


# --- HÀM ĐÃ ĐƯỢC SỬA LẠI ĐỂ TRẢ VỀ STRING ---
async def change_password(
    db: AsyncSession, user_id: int, current_password: str, new_password: str
) -> str:
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return "user_not_found" # Trả về chuỗi để Router biết user ko tồn tại
    
    # Verify current password
    if not verify_password(current_password, db_user.hashed_password):
        return "incorrect_password" # Trả về chuỗi để Router biết sai pass cũ
    
    # Update password
    db_user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(db_user)
    
    return "success" # Trả về chuỗi success