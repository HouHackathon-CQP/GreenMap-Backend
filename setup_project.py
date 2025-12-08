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

import os
import time
import subprocess
import sys
import httpx
import asyncio

# Cấu hình màu sắc cho đẹp
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def print_step(msg):
    print(f"{Colors.HEADER}=== {msg} ==={Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def check_env_file():
    print_step("1. Kiểm tra file .env")
    if not os.path.exists(".env"):
        print(f"{Colors.WARNING}⚠️ Chưa thấy file .env. Đang tạo từ env.example...{Colors.ENDC}")
        try:
            with open("env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print_success("Đã tạo file .env. Vui lòng cập nhật OPENAQ_API_KEY sau.")
        except Exception as e:
            print_error(f"Không thể tạo file .env: {e}")
            sys.exit(1)
    else:
        print_success("File .env đã tồn tại.")

async def wait_for_services():
    print_step("2. Chờ các dịch vụ Docker khởi động (Postgres & Orion)")
    
    orion_url = "http://localhost:1026/version"
    retries = 30
    
    print("⏳ Đang kết nối tới Orion-LD...")
    async with httpx.AsyncClient() as client:
        for i in range(retries):
            try:
                resp = await client.get(orion_url)
                if resp.status_code == 200:
                    print_success("Orion-LD đã sẵn sàng!")
                    return
            except httpx.ConnectError:
                pass
            
            print(f"   ... Đợi {i+1}/{retries}s")
            time.sleep(2)
    
    print_error("Quá thời gian chờ. Hãy kiểm tra 'docker-compose ps'.")
    sys.exit(1)

def run_command(command, description):
    print_step(f"Chạy: {description}")
    try:
        # Sử dụng sys.executable để đảm bảo dùng đúng python trong venv
        full_command = f"{sys.executable} {command}"
        result = subprocess.run(full_command, shell=True, check=True)
        if result.returncode == 0:
            print_success(f"Hoàn thành: {description}")
    except subprocess.CalledProcessError:
        print_error(f"Lỗi khi chạy: {description}")
        # Không exit để thử chạy các bước tiếp theo (tùy chọn)

async def main():
    print(f"{Colors.OKBLUE}🚀 BẮT ĐẦU CÀI ĐẶT HỆ THỐNG GREENMAP{Colors.ENDC}\n")
    
    # 1. Check .env
    check_env_file()

    # 2. Check Docker
    await wait_for_services()

    # 3. Quy trình nạp dữ liệu chuẩn
    print(f"\n{Colors.OKBLUE}--- BẮT ĐẦU NẠP DỮ LIỆU ---{Colors.ENDC}")
    
    # Bước 3.1: Tạo bảng & Admin
    run_command("init_db.py", "Khởi tạo Database & Admin")

    # Bước 3.2: Xử lý dữ liệu JSON lớn (Giao thông)
    run_command("Data/merge_json.py", "Gộp file dữ liệu mô phỏng")

    # Bước 3.3: Nạp bản đồ nền (Công viên, Trạm sạc...) vào Postgres
    run_command("import_osm.py", "Import GeoJSON vào PostgreSQL")

    # Bước 3.4: Đồng bộ bản đồ từ Postgres sang Orion
    run_command("sync_to_orion.py", "Đồng bộ dữ liệu sang Orion-LD")

    # Bước 3.5: Nạp dữ liệu Giao thông vào Postgres
    run_command("process_simulation.py", "Xử lý & Nạp dữ liệu Giao thông")
    
    # Bước 3.6: Đăng ký Sensor (Cần mạng internet để gọi OpenAQ)
    run_command("seed_sensor.py", "Đăng ký Thiết bị Cảm biến (Sensor)")

    print(f"\n{Colors.OKGREEN}🎉 CÀI ĐẶT HOÀN TẤT! BẠN CÓ THỂ CHẠY SERVER NGAY.{Colors.ENDC}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nĐã hủy cài đặt.")