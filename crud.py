from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas # Import "khuôn"

# ----------------------------------------------------------------
# HÀM TẠO MỚI (CREATE)
# ----------------------------------------------------------------
async def create_location(db: AsyncSession, location: schemas.LocationCreate):
    """
    Hàm "tay bẩn" đây:
    1. Nhận "khuôn" LocationCreate (có lat/lon).
    2. "Dịch" lat/lon thành WKT (Well-Known Text) mà PostGIS hiểu.
    3. Tạo object models.GreenLocation.
    4. Lưu vào CSDL.
    """
    
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
async def get_location(db: AsyncSession, location_id: int):
    """Lấy 1 địa điểm theo ID"""
    result = await db.execute(
        select(models.GreenLocation).where(models.GreenLocation.id == location_id)
    )
    return result.scalar_one_or_none() # Trả về 1 object, hoặc None

async def get_locations(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Lấy danh sách địa điểm (có phân trang)"""
    result = await db.execute(
        select(models.GreenLocation).offset(skip).limit(limit)
    )
    return result.scalars().all() # Trả về list[GreenLocation]