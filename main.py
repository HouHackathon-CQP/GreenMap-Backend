from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typing import List 
import uvicorn
import models
import schemas
import crud
from database import get_db, engine, Base


# HÀM KHỞI TẠO CSDL (Tạo bảng)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

app = FastAPI(
    title="Green Map Hanoi API",
    description="Backend API cho dự án Bản Đồ Xanh và OLP 2025."
)

@app.on_event("startup")
async def on_startup():
    print("Đang khởi tạo CSDL và các bảng...")
    await create_db_and_tables()
    print("Khởi tạo xong!")

# API CHO "ĐIỂM XANH" (GreenLocation)

@app.post("/locations", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để TẠO MỚI một "Điểm xanh" hoặc "Trạm sạc".
    Frontend sẽ gửi JSON khớp với khuôn 'LocationCreate'.
    API sẽ trả về dữ liệu khớp với khuôn 'LocationRead'.
    """
    return await crud.create_location(db=db, location=location)


@app.get("/locations", response_model=List[schemas.LocationRead])
async def read_all_locations(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để LẤY DANH SÁCH tất cả các địa điểm.
    Có hỗ trợ phân trang (skip, limit).
    """
    locations = await crud.get_locations(db=db, skip=skip, limit=limit)
    return locations


@app.get("/locations/{location_id}", response_model=schemas.LocationRead)
async def read_one_location(
    location_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để LẤY CHI TIẾT 1 địa điểm theo ID.
    """
    db_location = await crud.get_location(db=db, location_id=location_id)
    if db_location is None:
        # Nếu không tìm thấy, trả lỗi 404 cho Frontend
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

# API "KIỂM TRA SỨC KHỎE" 

@app.get("/")
async def get_root():
    return {"message": "Green Map Backend đang hoạt động!"}

@app.get("/test-db")
async def test_database_connection(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Kết nối CSDL PostGIS thành công!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# server config

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)