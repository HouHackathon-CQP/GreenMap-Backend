# HCMConnect-Backend/main.py

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
from fastapi.middleware.cors import CORSMiddleware

# (Tạo bảng... giữ nguyên)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

app = FastAPI(
    title="Green Map Hanoi API",
    description="Backend API cho dự án Bản Đồ Xanh và OLP 2025."
)

# (CORS... giữ nguyên)
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    print("Đang khởi tạo CSDL và các bảng...")
    await create_db_and_tables()
    print("Khởi tạo xong!")

@app.get("/locations", response_model=List[schemas.LocationRead])
async def read_all_locations(
    location_type: Optional[LocationType] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db)
):
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
    db_location = await db.get(models.GreenLocation, location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location

@app.post("/locations", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate, 
    db: AsyncSession = Depends(get_db)
):
    return await crud.create_location(db=db, location=location)

@app.post("/users", response_model=schemas.UserRead)
async def create_new_user(
    user: schemas.UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)

@app.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/aqi/hanoi")
async def get_live_hanoi_aqi():
    aqi_data = await services.get_hanoi_aqi()
    return {"source": "OpenAQ", "count": len(aqi_data), "data": aqi_data}

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)