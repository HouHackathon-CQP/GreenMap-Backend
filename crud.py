from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from security import get_password_hash
import models
import schemas 
from models import LocationType, User, UserRole
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


async def create_user(db: AsyncSession, user: schemas.UserCreate, role: UserRole = UserRole.CITIZEN):
    """
    Tạo user mới.
    - Mặc định 'role' là CITIZEN (nếu gọi từ API đăng ký).
    - Có thể truyền 'role=ADMIN' (nếu gọi từ script khởi tạo).
    """
    hashed_password = get_password_hash(user.password)
    
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=role 
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

# 1. TẠO BÁO CÁO
async def create_report(db: AsyncSession, report: schemas.ReportCreate, user_id: int):
    db_report = models.UserReport(
        **report.model_dump(), # Copy toàn bộ dữ liệu từ schema
        user_id=user_id,       # Gán ID người gửi
        status=models.ReportStatus.PENDING # Mặc định là chờ duyệt
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report

# 2. LẤY DANH SÁCH BÁO CÁO (Cho Admin)
async def get_reports(db: AsyncSession, status: models.ReportStatus = None, skip: int = 0, limit: int = 100):
    query = select(models.UserReport)
    if status:
        query = query.where(models.UserReport.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# 3. CẬP NHẬT TRẠNG THÁI (Duyệt bài)
async def update_report_status(db: AsyncSession, report_id: int, status: models.ReportStatus):
    # Tìm báo cáo
    result = await db.execute(select(models.UserReport).where(models.UserReport.id == report_id))
    db_report = result.scalar_one_or_none()
    
    if not db_report:
        return None
    
    # Cập nhật trạng thái
    db_report.status = status
    await db.commit()
    await db.refresh(db_report)
    return db_report