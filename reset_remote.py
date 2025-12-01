import asyncio
import httpx
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

# 1. DANH SÁCH CÁC BẢNG TRONG POSTGRES CẦN XÓA
# Thứ tự quan trọng: Xóa bảng con (có Foreign Key) trước, bảng cha sau
POSTGRES_TABLES = [
    "green_actions",      # Con của User
    "user_reports",       # Con của User
    "simulation_frames",  # Con của TrafficSegment
    "traffic_segments",
    "green_locations",
    "users"
]

# 2. CẤU HÌNH ORION
ORION_ENTITIES_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
HEADERS = {
    "Accept": "application/ld+json",
    # Dùng Link header chung nhất hoặc lấy từ settings
    "Link": '<https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
}

async def reset_postgres():
    print("\n--- 🗑️  BẮT ĐẦU DỌN DẸP POSTGRESQL ---")
    async with engine.begin() as conn:
        for table in POSTGRES_TABLES:
            print(f"   -> Đang xóa bảng: {table}...")
            # Dùng CASCADE để xóa các ràng buộc liên quan
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    print("✅ PostgreSQL đã sạch bóng!")

async def reset_orion():
    print("\n--- 🗑️  BẮT ĐẦU DỌN DẸP ORION-LD (QUA API) ---")
    async with httpx.AsyncClient() as client:
        while True:
            # Lấy 100 thực thể bất kỳ
            try:
                response = await client.get(
                    f"{ORION_ENTITIES_URL}?limit=100", 
                    headers=HEADERS
                )
                if response.status_code == 404: # Không còn gì
                    break
                    
                entities = response.json()
                if not entities:
                    print("   -> Orion đã trống rỗng.")
                    break

                print(f"   -> Tìm thấy {len(entities)} thực thể. Đang xóa...")
                
                # Xóa song song cho nhanh
                tasks = []
                for entity in entities:
                    entity_id = entity["id"]
                    tasks.append(client.delete(f"{ORION_ENTITIES_URL}/{entity_id}", headers=HEADERS))
                
                await asyncio.gather(*tasks)
                print(f"      Đã xóa xong lô này.")
                
            except Exception as e:
                print(f"❌ Lỗi khi xóa Orion: {e}")
                break

    print("✅ Orion-LD đã sạch bóng!")

async def main():
    # Chạy cả 2 nhiệm vụ
    await reset_postgres()
    await reset_orion()
    print("\n🎉 HOÀN TẤT RESET HỆ THỐNG! HÃY CHẠY LẠI CÁC SCRIPT INIT.")

if __name__ == "__main__":
    asyncio.run(main())