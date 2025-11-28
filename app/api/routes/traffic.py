import time
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(prefix="/traffic", tags=["traffic"])

# Cấu hình mô phỏng
LOOP_DURATION = 3600 
START_TIME_REF = time.time()
DATA_INTERVAL = 10 

@router.get("/segments")
async def get_static_map(db: AsyncSession = Depends(get_db)):
    """
    API 1: Lấy bản đồ nền (GeoJSON) - ĐÃ TỐI ƯU.
    - ST_Simplify(geom, 0.0001): Làm mượt đường, giảm điểm thừa (~11m).
    - ST_AsGeoJSON(..., 6): Giới hạn 6 số thập phân để giảm dung lượng.
    """
    query = """
        SELECT 
            id, 
            ST_AsGeoJSON(ST_Simplify(geom, 0.0001), 6) as geometry 
        FROM traffic_segments
    """
    result = await db.execute(text(query))
    
    features = []
    for row in result.mappings():
        geom_str = row.geometry
        if not geom_str: continue
        geom = json.loads(geom_str)
        segment_name = f"Đoạn đường {row.id}"
        
        features.append({
            "type": "Feature",
            "id": str(row.id),
            "geometry": geom,
            "properties": {
                "id": str(row.id), 
                "name": segment_name
            }
        })
        
    return {"type": "FeatureCollection", "features": features}

@router.get("/live")
async def get_live_status(db: AsyncSession = Depends(get_db)):
    """
    API 2: Lấy trạng thái hiện tại.
    Tự động làm tròn thời gian xuống mốc 10s gần nhất.
    """

    raw_second = int(time.time() - START_TIME_REF) % LOOP_DURATION
    query_second = (raw_second // DATA_INTERVAL) * DATA_INTERVAL
    query = """
        SELECT segment_id, status_color 
        FROM simulation_frames 
        WHERE time_second = :sec
    """
    result = await db.execute(text(query), {"sec": query_second})
    status_map = {str(row.segment_id): row.status_color for row in result.mappings()}
    return {
        "time_real": raw_second,
        "time_query": query_second,
        "status": status_map
    }