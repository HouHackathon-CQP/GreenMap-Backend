import sys
import asyncio
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text 
from typing import List, Optional
import logging
import shutil
import uuid
import os
from fastapi.staticfiles import StaticFiles
import httpx 
from config import ORION_BROKER_URL
import uuid
from fastapi import File, UploadFile, BackgroundTasks

# --- [FIX WINDOWS] ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("--- [SYSTEM] Đã kích hoạt WindowsSelectorEventLoopPolicy ---")
# ---------------------

# Import các module của bạn
import models
import schemas
import crud
from database import engine, get_db, Base
from dependencies import get_current_user, get_current_admin
import services

# Cấu hình log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo bảng CSDL (Async)
async def create_db_and_tables():
    print("Đang khởi tạo CSDL và các bảng...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;")) 
    print("Khởi tạo xong!")

# Khởi tạo App
app = FastAPI()

# Tạo thư mục chứa ảnh nếu chưa có
if not os.path.exists("static/images"):
    os.makedirs("static/images")

# "Mount" thư mục này ra ngoài để xem ảnh qua URL (http://.../static/...)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

# --- CÁC API ---

@app.get("/")
async def root():
    return {"message": "GreenMap Backend is Running!"}

@app.get("/test-db")
async def test_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1")) 
        return {"status": "Database Connected Successfully"}
    except Exception as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")

@app.post("/users", response_model=schemas.UserRead)
async def create_new_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)

# API Login
from fastapi.security import OAuth2PasswordRequestForm
from security import create_access_token, verify_password

@app.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Login attempt for: {form_data.username}")
    user = await crud.get_user_by_email(db, email=form_data.username)
    
    if not user:
        logger.warning("User not found")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning("Password mismatch")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/locations", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    print(f"Admin đang tạo: {current_user.email}")
    return await crud.create_location(db=db, location=location)

@app.get("/locations", response_model=List[schemas.LocationRead])
async def read_all_locations(
    location_type: Optional[models.LocationType] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_locations(db=db, location_type=location_type, skip=skip, limit=limit)

@app.get("/aqi/hanoi")
async def get_live_hanoi_aqi():
    """
    Lấy dữ liệu AQI từ 'bộ não' Orion-LD.
    """
    # URL của Orion-LD
    orion_url = f"{ORION_BROKER_URL}/ngsi-ld/v1/entities"
    
    params = {
        "type": "AirQualityObserved", 
        "limit": 100, # <-- QUAN TRỌNG: Lấy tối đa 100 trạm
        # "options": "keyValues" # Bỏ comment nếu muốn dữ liệu gọn hơn
    }
    
    # --- QUAN TRỌNG: Headers bắt buộc ---
    # Thiếu dòng 'Link' này là Orion sẽ trả về danh sách rỗng
    headers = {
        "Accept": "application/ld+json",
        "Link": '<https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
    }

    try:
        async with httpx.AsyncClient() as client:
            # Gọi sang Orion-LD (Port 1026)
            response = await client.get(orion_url, params=params, headers=headers)
            response.raise_for_status()
            
            orion_data = response.json()
            
            return {
                "source": "Orion-LD Context Broker",
                "count": len(orion_data),
                "data": orion_data
            }
            
    except Exception as e:
        return {
            "source": "Orion-LD (Error)",
            "error": str(e),
            "hint": "Kiểm tra container 'greenmap-orion' hoặc header Link."
        }
    
# --- API UPLOAD ẢNH ---
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload ảnh lên server. Trả về URL để lưu vào báo cáo.
    """
    # 1. Đổi tên file thành UUID để không bị trùng
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/images/{file_name}"
    
    # 2. Lưu file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Trả về đường dẫn
    return {"url": f"/static/images/{file_name}"}

# --- API TẠO BÁO CÁO (Người dân) ---
@app.post("/reports", response_model=schemas.ReportRead)
async def create_new_report(
    report: schemas.ReportCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Bắt buộc đăng nhập
):
    """
    Người dân gửi báo cáo sự cố/ô nhiễm.
    """
    return await crud.create_report(db=db, report=report, user_id=current_user.id)

# --- API XEM DANH SÁCH BÁO CÁO (Admin) ---
@app.get("/reports", response_model=List[schemas.ReportRead])
async def read_reports(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin) # Chỉ Admin mới được xem
):
    """
    Admin xem danh sách các báo cáo để duyệt.
    """
    return await crud.get_reports(db=db, skip=skip, limit=limit)

# --- API UPLOAD ẢNH (Lưu local đơn giản) ---
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/images/{file_name}"
    
    # Lưu file (Đảm bảo thư mục static/images đã tồn tại)
    with open(file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
        
    return {"url": f"/static/images/{file_name}"}

# --- API GỬI BÁO CÁO (Người dân) ---
@app.post("/reports", response_model=schemas.ReportRead)
async def create_new_report(
    report: schemas.ReportCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Cần đăng nhập
):
    return await crud.create_report(db=db, report=report, user_id=current_user.id)

# --- API XEM BÁO CÁO (Admin/Manager) ---
@app.get("/reports", response_model=List[schemas.ReportRead])
async def read_reports(
    status: Optional[models.ReportStatus] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin) # Chỉ Admin xem
):
    return await crud.get_reports(db=db, status=status, skip=skip, limit=limit)

# --- HÀM PHỤ TRỢ: ĐẨY BÁO CÁO SANG ORION-LD ---
async def push_report_to_orion(report: models.UserReport):
    """
    Hàm này sẽ chuyển đổi báo cáo từ Postgres -> NGSI-LD Entity -> Gửi sang Orion
    (Đã sửa lỗi 'value: null')
    """
    orion_url = f"{ORION_BROKER_URL}/ngsi-ld/v1/entities"
    
    entity_id = f"urn:ngsi-ld:CivicIssue:Hanoi:{report.id}"

    payload = {
        "id": entity_id,
        "type": "CivicIssue",
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [report.longitude, report.latitude]
            }
        },
        "status": {
            "type": "Property",
            "value": "open"
        },
        "reportDate": {
            "type": "Property",
            "value": report.created_at
        },
        "name": {
            "type": "Property",
            "value": report.title
        },
        "@context": "https://schema.lab.fiware.org/ld/context"
    }
    
    # 2. KIỂM TRA VÀ THÊM CÁC TRƯỜNG TÙY CHỌN (Optional)
    # Chỉ thêm nếu có dữ liệu (khác None/Empty)
    if report.description:
        payload["description"] = {
            "type": "Property",
            "value": report.description
        }
        
    if report.image_url:
        payload["image"] = {
            "type": "Property",
            "value": report.image_url
        }
    
    headers = {"Content-Type": "application/ld+json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(orion_url, json=payload, headers=headers)
            if response.status_code in [201, 409]: 
                print(f"✅ Đã đẩy báo cáo {report.id} sang Orion-LD thành công!")
            else:
                print(f"❌ Lỗi đẩy Orion: {response.text}")
        except Exception as e:
             print(f"❌ Lỗi kết nối Orion: {e}")

# --- API DUYỆT BÁO CÁO (Admin) ---
@app.put("/reports/{report_id}/status", response_model=schemas.ReportRead)
async def approve_report(
    report_id: int,
    status_update: schemas.ReportUpdate, # Body chứa {"status": "APPROVED"}
    background_tasks: BackgroundTasks,   # Để chạy tác vụ ngầm
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    # 1. Cập nhật trong Postgres
    report = await crud.update_report_status(db, report_id, status_update.status)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 2. Nếu trạng thái là APPROVED -> Đẩy sang Orion
    if status_update.status == models.ReportStatus.APPROVED:
        # Dùng BackgroundTasks để không làm user phải chờ việc đẩy dữ liệu
        background_tasks.add_task(push_report_to_orion, report)
        
    return report

# --- CHẠY SERVER ---
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)