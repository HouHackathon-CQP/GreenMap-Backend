# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os


# Lý do có file này là do file gốc > 100mb không push lên GitHub được.
# Nên ta sẽ tách file lớn này thành 2 phần nhỏ hơn để push.
# Cấu hình tên file
INPUT_FILE = 'Data\simulation_data.json'
OUTPUT_PART1 = 'Data\simulation_data_part1.json'
OUTPUT_PART2 = 'Data\simulation_data_part2.json'

def split_json():
    print(f"⏳ Đang đọc file lớn '{INPUT_FILE}' (có thể mất vài giây)...")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        total_items = len(data)
        print(f"📊 Tổng số dòng dữ liệu: {total_items}")
        
        # Tính vị trí giữa để cắt
        mid_point = total_items // 2
        
        # Tách dữ liệu
        part1 = data[:mid_point]
        part2 = data[mid_point:]
        
        print(f"✂️ Đang cắt file...")
        print(f"   - Phần 1: {len(part1)} dòng")
        print(f"   - Phần 2: {len(part2)} dòng")

        # Lưu phần 1
        print(f"💾 Đang lưu '{OUTPUT_PART1}'...")
        with open(OUTPUT_PART1, 'w', encoding='utf-8') as f:
            json.dump(part1, f, indent=2) # indent=2 để dễ nhìn, bỏ đi nếu muốn file nhẹ hơn

        # Lưu phần 2
        print(f"💾 Đang lưu '{OUTPUT_PART2}'...")
        with open(OUTPUT_PART2, 'w', encoding='utf-8') as f:
            json.dump(part2, f, indent=2)

        print("✅ HOÀN TẤT! Đã tách thành công.")

    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file '{INPUT_FILE}'")
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    split_json()