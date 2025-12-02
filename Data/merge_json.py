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
# Nên ta sẽ nối 2 phần nhỏ lại thành file gốc.

# Cấu hình tên file
PART1_FILE = 'Data\simulation_data_part1.json'
PART2_FILE = 'Data\simulation_data_part2.json'
OUTPUT_FILE = 'Data\simulation_data.json'

def merge_json():
    print("⏳ Đang tiến hành nối file...")
    full_data = []

    try:
        # Đọc phần 1
        if os.path.exists(PART1_FILE):
            print(f"📖 Đang đọc '{PART1_FILE}'...")
            with open(PART1_FILE, 'r', encoding='utf-8') as f:
                data1 = json.load(f)
                full_data.extend(data1)
        else:
            print(f"❌ Lỗi: Không tìm thấy '{PART1_FILE}'")
            return

        # Đọc phần 2
        if os.path.exists(PART2_FILE):
            print(f"📖 Đang đọc '{PART2_FILE}'...")
            with open(PART2_FILE, 'r', encoding='utf-8') as f:
                data2 = json.load(f)
                full_data.extend(data2)
        else:
            print(f"❌ Lỗi: Không tìm thấy '{PART2_FILE}'")
            return

        print(f"📊 Tổng số dòng sau khi gộp: {len(full_data)}")

        # Lưu file gộp
        print(f"💾 Đang lưu file gộp '{OUTPUT_FILE}'...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, indent=2)

        print("✅ HOÀN TẤT! File gốc đã được khôi phục.")

    except Exception as e:
        print(f"❌ Lỗi khi nối file: {e}")

if __name__ == "__main__":
    merge_json()