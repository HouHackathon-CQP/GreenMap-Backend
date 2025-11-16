import json
import asyncio
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from shapely.geometry import shape
from pathlib import Path 
from sqlalchemy.sql import text 

# Import các thành phần CSDL và Model
from database import SessionLocal, engine 
from models import GreenLocation, LocationType, Base
CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = CURRENT_FILE_PATH.parent
DATA_DIR = PROJECT_DIR.parent / "HCMConnect-Data" / "Data"


async def create_location_from_feature(db, feature: dict, location_type: LocationType):
    properties = feature.get("properties", {})
    geometry = feature.get("geometry")
    if not geometry: return
    
    name = properties.get("name")
    external_id = properties.get("@id")
    
    if not name: 
        # Lấy tạm tên từ 'description' nếu có
        name = properties.get("description", external_id) # Lấy external_id làm tên cuối cùng
        
    if not name: # Nếu vẫn không có tên
        name = f"{location_type.value}_{external_id}" # Tên dự phòng

    geom_shape = shape(geometry)
    centroid = geom_shape.centroid
    
    longitude = centroid.x
    latitude = centroid.y
    
    wkt_location = f"SRID=4326;POINT({longitude} {latitude})"

    existing = await db.execute(
        select(GreenLocation).where(GreenLocation.external_id == external_id)
    )
    if existing.scalar_one_or_none():
        print(f"Bỏ qua (đã tồn tại): {name[:50]}...") 
        return

    db_location = GreenLocation(
        name=str(name), # Ép kiểu về string
        location_type=location_type,
        location=wkt_location,
        description=str(properties.get("description")), # Ép kiểu về string
        data_source="OpenStreetMap",
        external_id=external_id,
        is_active=True
    )
    db.add(db_location)
    print(f"Thêm mới: {name[:50]}...") # Cắt ngắn tên cho gọn

async def seed():
    if not DATA_DIR.exists():
        print(f"LỖI: Không tìm thấy thư mục data tại: {DATA_DIR}")
        print("Vui lòng kiểm tra lại cấu trúc thư mục.")
        return # Thoát script nếu không tìm thấy data
    
    print(f"Sẽ đọc dữ liệu từ: {DATA_DIR}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

    db = SessionLocal()
    try:
        # [cite_start]1. Bơm TRẠM SẠC [cite: 1986-2590]
        print("\n--- Đang bơm dữ liệu TRẠM SẠC ---")
        charging_file = DATA_DIR / "charging_station.geojson"
        with open(charging_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feature in data['features']:
                await create_location_from_feature(db, feature, LocationType.CHARGING_STATION)

        # [cite_start]2. Bơm ĐIỂM THUÊ XE ĐẠP [cite: 3404-3610]
        print("\n--- Đang bơm dữ liệu THUÊ XE ĐẠP ---")
        bicycle_file = DATA_DIR / "bicycle_rental.geojson"
        with open(bicycle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feature in data['features']:
                await create_location_from_feature(db, feature, LocationType.BICYCLE_RENTAL)

        # [cite_start]3. Bơm CÔNG VIÊN (PUBLIC_PARK) [cite: 2611-3403]
        print("\n--- Đang bơm dữ liệu CÔNG VIÊN ---")
        park_file = DATA_DIR / "park.geojson"
        with open(park_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feature in data['features']:
                await create_location_from_feature(db, feature, LocationType.PUBLIC_PARK)
        
        # 4. Bơm ĐỊA ĐIỂM DU LỊCH (ATTRACTION) [cite: 1-1985]
        print("\n--- Đang bơm dữ liệu ĐỊA ĐIỂM DU LỊCH ---")
        tourist_file = DATA_DIR / "tourist_attractions.geojson"
        with open(tourist_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for feature in data['features']:
                await create_location_from_feature(db, feature, LocationType.TOURIST_ATTRACTION)
        
        await db.commit()
        print("\n--- HOÀN THÀNH BƠM DỮ LIỆU! ---")
    
    except FileNotFoundError as e:
        print(f"LỖI: Không tìm thấy file: {e.filename}")
        print(f"Hãy chắc chắn file của bạn nằm ở thư mục: {DATA_DIR}")
    except Exception as e:
        await db.rollback()
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        await db.close()
        
if __name__ == "__main__":
    asyncio.run(seed())