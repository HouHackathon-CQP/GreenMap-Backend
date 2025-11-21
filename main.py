import sys
import asyncio
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text  # <-- 1. IMPORT HÀM 'text' TỪ ĐÂY
from typing import List, Optional
import logging

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
        # --- 2. SỬA LỖI TẠI ĐÂY ---
        # Dùng trực tiếp 'text()', không phải 'models.text()'
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;")) 
        # --------------------------
    print("Khởi tạo xong!")

# Khởi tạo App
app = FastAPI()

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
        # Dùng text() ở đây nữa
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
    aqi_data = await services.get_hanoi_aqi()
    return {"source": "OpenAQ", "count": len(aqi_data), "data": aqi_data}

# --- CHẠY SERVER ---
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)