# 🌱 GreenMap Backend - Bản Đồ Xanh Hà Nội

> **Dự án xây dựng hệ thống backend cho ứng dụng Bản đồ xanh, tích hợp dữ liệu mở liên kết (Linked Open Data) và IoT thời gian thực theo tiêu chuẩn OLP 2025.**

---

## 🏗 Kiến Trúc Hệ Thống

Hệ thống sử dụng kiến trúc **Hybrid (Lai)** gồm 2 thành phần chính:

| Thành phần | Công nghệ | Chức năng |
| :--- | :--- | :--- |
| **Core Backend** | FastAPI + PostgreSQL | Quản lý người dùng, xác thực (Auth), và báo cáo sự cố (Citizen Report). |
| **Context Broker** | Orion-LD + MongoDB | "Bộ não" quản lý dữ liệu bản đồ và chỉ số AQI thời gian thực theo chuẩn **NGSI-LD** (SOSA/SSN). |

---

## 🚀 Hướng Dẫn Cài Đặt (Luồng Khởi Tạo)

### 1. Yêu Cầu Tiên Quyết (Prerequisites)
Đảm bảo máy tính của bạn đã cài đặt:
- [x] **Docker Desktop** (Bắt buộc để chạy Orion-LD và CSDL).
- [x] **Python 3.10+**.
- [x] **Git**.

### 2. Thiết Lập Môi Trường

**Bước 1: Clone repository**
```bash
git clone https://github.com/HouHackathon-CQP/GreenMap-Backend.git
cd GreenMap-Backend
```

**Bước 2: Tạo môi trường ảo (Virtual Environment)**

*Windows:*
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

*Mac/Linux:*
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Bước 3: Cài đặt thư viện**
```bash
pip install -r requirements.txt
```

**Bước 4: Cấu hình biến môi trường**
Tạo file `.env` tại thư mục gốc và copy nội dung sau:

```env
# --- Cấu hình Database & Auth ---
DATABASE_URL="postgresql+asyncpg://admin:mysecretpassword@127.0.0.1:5432/greenmap_db"
SECRET_KEY="thay_the_bang_chuoi_bi_mat_cua_ban" #64 chars 
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# --- Tài khoản Admin mặc định ---
FIRST_SUPERUSER="admin@greenmap.hanoi"
FIRST_SUPERUSER_PASSWORD="123456"

# --- Cấu hình IoT & Open Data ---
OPENAQ_API_KEY="your_openaq_api_key_here"
ORION_BROKER_URL="http://localhost:1026"
```

### 3. Khởi Động Hạ Tầng (Docker)
Chạy lệnh sau để bật CSDL (PostGIS, MongoDB) và Context Broker (Orion-LD):

```bash
docker-compose up -d
```
> ⏳ **Lưu ý:** Chờ khoảng 10-15 giây để các container khởi động hoàn toàn trước khi sang bước tiếp theo.

### 4. Khởi Tạo Dữ Liệu (Quan Trọng)
Chạy lần lượt các script sau để nạp dữ liệu mẫu vào hệ thống:

**4.1. Khởi tạo bảng User & Admin** (PostgreSQL)
```bash
python init_db.py
```
*Kết quả mong đợi:* In ra `--- Tạo Admin thành công! ---`.

**4.2. Đăng ký Thiết bị cảm biến** (Orion-LD)
```bash
python seed_sensors.py
```

**4.3. Nạp dữ liệu Bản đồ tĩnh** (Orion-LD)
```bash
python seed_data.py
```

---

## 🏃‍♂️ Hướng Dẫn Chạy Server

Bạn cần mở **2 Terminal song song** để chạy toàn bộ hệ thống.

### Terminal 1: Chạy API Backend (FastAPI)
Phục vụ cho Mobile App/Web (Đăng nhập, Báo cáo...).

```bash
# Đảm bảo đã activate .venv
python main.py
```
* **Server URL:** `http://127.0.0.1:8000`
* **Swagger UI:** `http://127.0.0.1:8000/docs`

### Terminal 2: Chạy Đặc Vụ AQI (Realtime Agent)
Script chạy nền cập nhật chỉ số không khí từ OpenAQ về Orion-LD.

```bash
# Đảm bảo đã activate .venv
python aqi_agent.py
```
*Script sẽ chạy định kỳ và in log:* `Thành công! Đã 'upsert' ... thực thể.`

---

## 📡 Cách Truy Cập Dữ Liệu (Dành cho Frontend)

### 1. API Nghiệp vụ (User, Auth, Report)
Gọi trực tiếp vào **FastAPI**: `http://127.0.0.1:8000`
* **Đăng nhập:** `POST /login` (JSON body: `{ "email": "...", "password": "..." }`).
* **Gửi báo cáo:** `POST /reports` (Kèm Token Bearer).

### 2. API Dữ liệu Bản đồ & IoT (Orion-LD)
Gọi trực tiếp vào **Context Broker**: `http://localhost:1026/ngsi-ld/v1/entities`

> ⚠️ **LƯU Ý QUAN TRỌNG:** Mọi request gửi đến Orion-LD **BẮT BUỘC** phải có Headers sau:

```http
Accept: application/ld+json
Link: <https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"
```

**Ví dụ truy vấn:**

* Lấy tất cả trạm AQI:
    `GET .../entities?type=AirQualityObserved&limit=100`
* Lấy tất cả công viên:
    `GET .../entities?type=PUBLIC_PARK&limit=100`

---

## 🛠 Xử Lý Sự Cố (Troubleshooting)

* **Lỗi `WinError 121` hoặc `Socket hang up`:**
    * Restart lại server (`Ctrl+C` và chạy lại `python main.py`). Code đã tích hợp bản vá lỗi cho Windows.
* **Lỗi kết nối Database:**
    * Chạy `docker-compose down` sau đó `docker-compose up -d` để reset lại các container.
* **API trả về danh sách rỗng `[]`:**
    * Kiểm tra xem đã chạy `seed_data.py` chưa.
    * Kiểm tra Headers `Link` khi gọi Orion-LD đã đúng cú pháp chưa.
