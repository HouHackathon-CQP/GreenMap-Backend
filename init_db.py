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

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import crud, models, schemas
from app.core.config import settings
from app.db.session import AsyncSessionLocal, init_db


async def create_super_user(db: AsyncSession):
    email = settings.first_superuser
    password = settings.first_superuser_password

    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if user:
        print(f"--- Admin user {email} đã tồn tại. Bỏ qua. ---")
    else:
        print(f"--- Đang tạo Admin user: {email} ---")
        user_in = schemas.UserCreate(email=email, password=password, full_name="Super Admin")
        await crud.create_user(db, user_in, role=models.UserRole.ADMIN)
        print("--- Tạo Admin thành công! ---")


async def main():
    print("--- Bắt đầu khởi tạo hệ thống ---")
    await init_db()

    async with AsyncSessionLocal() as db:
        await create_super_user(db)

    print("--- Hoàn tất khởi tạo ---")


if __name__ == "__main__":
    asyncio.run(main())
