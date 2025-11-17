from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typing import List
import uvicorn
import models
import schemas
import crud
from database import get_db, engine, Base
from fastapi.security import OAuth2PasswordRequestForm
from security import create_access_token
from security import verify_password
import services
from typing import List, Optional
from models import LocationType

# --- THÊM IMPORT CHO CORS ---
from fastapi.middleware.cors import CORSMiddleware

# HÀM KHỞI TẠO CSDL (Tạo bảng)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

app = FastAPI(
    title="Green Map Hanoi API",
    description="Backend API cho dự án Bản Đồ Xanh và OLP 2025."
)

# --- CORS ---

origins = [
    "http://localhost:5173", # Địa chỉ của React (Vite)
    "http://localhost:5174", # (Địa chỉ dự phòng của Vite)
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Chỉ cho phép các địa chỉ này
    allow_credentials=True,
    allow_methods=["*"],         # Cho phép mọi phương thức (GET, POST, v.v.)
    allow_headers=["*"],         # Cho phép mọi header
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
    location_type: Optional[LocationType] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để LẤY DANH SÁCH tất cả các địa điểm.
    Giờ đã hỗ trợ lọc theo 'location_type'.
    """
    locations = await crud.get_locations(
        db=db, 
        location_type=location_type,
        skip=skip, 
        limit=limit
    )
    return locations


@app.get("/locations/{location_id}", response_model=schemas.LocationRead)
async def read_one_location(
    location_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để LẤY CHI TIẾT 1 địa điểm theo ID.
    """
    db_location = await crud.get_location(db=db, location_id=location_id) # Giả định crud.py có hàm này
    if db_location is None:
        # Nếu không tìm thấy, trả lỗi 404 cho Frontend
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

# API CHO "USER"
@app.post("/users", response_model=schemas.UserRead)
async def create_new_user(
    user: schemas.UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    API để ĐĂNG KÝ một người dùng mới.
    """
    # 1. Kiểm tra xem email đã tồn tại chưa?
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        # Nếu tồn tại, trả lỗi 400
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Nếu email OK, gọi 'crud' để tạo user (đã bao gồm băm mật khẩu)
    return await crud.create_user(db=db, user=user)

# ĐĂNG NHẬP và LẤY TOKEN
@app.post("/login")
async def login_for_access_token(
    # FastAPI sẽ tự động lấy 'username' và 'password' từ form
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    API để ĐĂNG NHẬP. Trả về một "Access Token".
    """
    
    # 1. Kiểm tra User: (form_data.username chính là 'email')
    user = await crud.get_user_by_email(db, email=form_data.username)
    
    # 2. Kiểm tra Mật khẩu:
    #    So sánh pass "chay" (form_data.password) với pass "băm" (user.hashed_password)
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Nếu sai, trả lỗi 401
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Đây là chuẩn
        )
        
    # 3. Mật khẩu đúng! Tạo "vé thông hành" (JWT)
    #    "sub" (subject) chính là email của user
    access_token = create_access_token(
        data={"sub": user.email}
    )
    
    # 4. Trả "vé" về cho Frontend
    return {"access_token": access_token, "token_type": "bearer"}


# API LẤY DỮ LIỆU AQI THỜI GIAN THỰC CHO HÀ NỘI
@app.get("/aqi/hanoi")
async def get_live_hanoi_aqi():
    """
    API lấy dữ liệu AQI (pm2.5) thời gian thực cho Hà Nội từ OpenAQ.
    """
    aqi_data = await services.get_hanoi_aqi()
    return {"source": "OpenAQ", "count": len(aqi_data), "data": aqi_data}

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