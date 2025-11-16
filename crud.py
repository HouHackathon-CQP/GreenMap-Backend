from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from security import get_password_hash
import models
import schemas 
from models import LocationType 
from typing import Optional

# ----------------------------------------------------------------
# HÀM TẠO MỚI (CREATE)
# ----------------------------------------------------------------
async def create_location(db: AsyncSession, location: schemas.LocationCreate):
    """Tạo mới một địa điểm (GreenLocation) trong CSDL"""
    # "Dịch" lat/lon thành WKT. Ví dụ: "SRID=4326;POINT(105.8 21.0)"
    wkt_location = f"SRID=4326;POINT({location.longitude} {location.latitude})"
    
    # Tạo object model
    db_location = models.GreenLocation(
        name=location.name,
        location_type=location.location_type,
        description=location.description,
        location=wkt_location # Đây là trường Geometry
    )
    
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    
    return db_location # Trả về object model

# ----------------------------------------------------------------
# HÀM ĐỌC (READ)
# ----------------------------------------------------------------
async def get_locations(
    db: AsyncSession, 
    location_type: Optional[LocationType] = None, # <-- Thêm tham số lọc
    skip: int = 0, 
    limit: int = 100
):
    """Lấy danh sách địa điểm (có phân trang VÀ LỌC)"""
    
    # Bắt đầu câu truy vấn
    query = select(models.GreenLocation)
    
    # Nếu người dùng cung cấp bộ lọc, thêm điều kiện WHERE
    if location_type:
        query = query.where(models.GreenLocation.location_type == location_type)
        
    # Thêm phân trang và thực thi
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all() # Trả về list[GreenLocation]


# user CRUD functions
async def get_user_by_email(db: AsyncSession, email: str):
    """Lấy 1 user theo email (dùng để kiểm tra email tồn tại)"""
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: schemas.UserCreate):
    """
    Hàm "tay bẩn" để tạo user:
    1. Nhận "khuôn" UserCreate (có password "chay").
    2. "Băm" mật khẩu.
    3. Tạo object models.User.
    4. Lưu vào CSDL.
    """
    
    # 2. "Băm" mật khẩu
    hashed_password = get_password_hash(user.password)
    
    # 3. Tạo object model
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password # LƯU MẬT KHẨU ĐÃ BĂM
    )
    
    # 4. Lưu vào CSDL
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user # Trả về object model