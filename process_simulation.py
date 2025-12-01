import json
import asyncio
import statistics
from sqlalchemy import text
from app.db.session import engine

INPUT_FILE = 'Data\simulation_data.json'
BATCH_SIZE = 2000 # Kích thước lô: 2000 dòng chèn 1 lần

async def process_data():
    print("--- 🚀 BẮT ĐẦU XỬ LÝ DỮ LIỆU MÔ PHỎNG (CHẾ ĐỘ BATCH) ---")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file {INPUT_FILE}")
        return

    print(f"📂 Đã đọc {len(raw_data)} dòng dữ liệu.")

    # 1. Tái tạo hình học
    print("1️⃣ Đang tái tạo hình học đường đi từ vết xe...")
    segments_points = {}
    for item in raw_data:
        lane = item['lane_id']
        if lane.startswith(":"): continue 
        if lane not in segments_points:
            segments_points[lane] = []
        segments_points[lane].append((item['lon'], item['lat']))

    # 2. Tính toán frames
    print("2️⃣ Đang tính toán trạng thái giao thông từng giây...")
    frames_data = {} 
    for item in raw_data:
        t = item['time_sec']
        lane = item['lane_id']
        if lane.startswith(":"): continue
        
        if t not in frames_data: frames_data[t] = {}
        if lane not in frames_data[t]: frames_data[t][lane] = []
        frames_data[t][lane].append(item['speed'])

    # 3. Lưu vào Database
    print("3️⃣ Bắt đầu ghi vào PostgreSQL (Batch Insert)...")
    
    async with engine.begin() as conn:
        # A. Xóa cũ
        print("   -> Làm sạch bảng cũ...")
        await conn.execute(text("TRUNCATE TABLE simulation_frames, traffic_segments CASCADE"))
        
        # B. Lưu TrafficSegments
        print(f"   -> Đang chuẩn bị {len(segments_points)} đoạn đường...")
        saved_segment_ids = set()
        segment_params = []
        
        for lane_id, points in segments_points.items():
            unique_points = sorted(list(set(points)))
            if len(unique_points) < 2: continue
            
            # Lấy mẫu để vẽ đường
            path_points = unique_points
            
            # Tạo chuỗi WKT
            wkt_coords = ", ".join([f"{p[0]} {p[1]}" for p in path_points])
            wkt = f"LINESTRING({wkt_coords})"
            
            segment_params.append({"id": lane_id, "wkt": wkt})
            saved_segment_ids.add(lane_id)
            
            # Thực thi Batch nếu đầy
            if len(segment_params) >= BATCH_SIZE:
                await conn.execute(text("""
                    INSERT INTO traffic_segments (id, geom) 
                    VALUES (:id, ST_GeomFromText(:wkt, 4326))
                    ON CONFLICT (id) DO NOTHING
                """), segment_params)
                segment_params = [] # Reset lô
        
        # Nạp nốt lô cuối cùng
        if segment_params:
            await conn.execute(text("""
                INSERT INTO traffic_segments (id, geom) 
                VALUES (:id, ST_GeomFromText(:wkt, 4326))
                ON CONFLICT (id) DO NOTHING
            """), segment_params)

        # C. Lưu SimulationFrames
        print(f"   -> Đang chuẩn bị dữ liệu Frames...")
        frame_params = []
        total_frames_count = 0
        
        for t, lanes in frames_data.items():
            for lane_id, speeds in lanes.items():
                if lane_id not in saved_segment_ids: continue
                if not speeds: continue
                
                avg_spd = statistics.mean(speeds)
                
                if avg_spd < 5: color = "red"
                elif avg_spd < 20: color = "orange"
                else: color = "green"
                
                frame_params.append({
                    "t": t, 
                    "sid": lane_id, 
                    "spd": avg_spd, 
                    "color": color
                })
                
                # Thực thi Batch nếu đầy
                if len(frame_params) >= BATCH_SIZE:
                    await conn.execute(text("""
                        INSERT INTO simulation_frames (time_second, segment_id, avg_speed, status_color)
                        VALUES (:t, :sid, :spd, :color)
                    """), frame_params)
                    total_frames_count += len(frame_params)
                    print(f"      ... Đã nạp {total_frames_count} bản ghi frame")
                    frame_params = [] # Reset lô

        # Nạp nốt lô cuối cùng
        if frame_params:
            await conn.execute(text("""
                INSERT INTO simulation_frames (time_second, segment_id, avg_speed, status_color)
                VALUES (:t, :sid, :spd, :color)
            """), frame_params)
            print(f"      ... Đã nạp {total_frames_count + len(frame_params)} bản ghi frame")

    print("--- 🎉 HOÀN TẤT! TỐC ĐỘ TÊN LỬA! ---")

if __name__ == "__main__":
    asyncio.run(process_data())