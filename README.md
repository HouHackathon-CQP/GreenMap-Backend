# GreenMap Backend - Bản Đồ Xanh Hà Nội

Hệ thống backend cho ứng dụng Bản đồ xanh - tích hợp dữ liệu mở liên kết (Linked Open Data) và IoT theo tiêu chuẩn NGSI-LD.

## Mục Lục
- [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
- [Yêu Cầu Tiên Quyết](#yêu-cầu-tiên-quyết)
- [Cài Đặt](#cài-đặt)
- [Chạy Ứng Dụng](#chạy-ứng-dụng)
- [API Endpoints](#api-endpoints)
- [Xử Lý Sự Cố](#xử-lý-sự-cố)

---

## Kiến Trúc Hệ Thống

Hệ thống sử dụng kiến trúc Hybrid với 2 thành phần chính:

| Thành Phần | Công Nghệ | Chức Năng |
|---|---|---|
| **Core Backend** | FastAPI + PostgreSQL | Quản lý người dùng, xác thực, báo cáo sự cố |
| **Context Broker** | Orion-LD + MongoDB | Quản lý dữ liệu bản đồ và chỉ số AQI theo chuẩn NGSI-LD |

---

## Yêu Cầu Tiên Quyết

- Docker Desktop (bắt buộc)
- Python 3.10+
- Git

---

## Cài Đặt

### 1. Clone Repository
```bash
git clone https://github.com/HouHackathon-CQP/GreenMap-Backend.git
cd GreenMap-Backend
```

### 2. Tạo Virtual Environment

**Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu Hình Environment
Tạo file `.env` tại thư mục gốc:

```env
# Database & Authentication
DATABASE_URL="postgresql+asyncpg://admin:mysecretpassword@127.0.0.1:5432/greenmap_db"
SECRET_KEY="your_secret_key_here_min_64_chars"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
CORS_ORIGINS="http://localhost:3000"

# Admin Account
FIRST_SUPERUSER="admin@greenmap.hanoi"
FIRST_SUPERUSER_PASSWORD="123456"

# External APIs
OPENAQ_API_KEY="your_openaq_api_key"
ORION_BROKER_URL="http://localhost:1026"
```

### 5. Khởi Động Docker
```bash
docker-compose up -d
```
⏳ Chờ 10-15 giây để các container khởi động hoàn toàn.

### 6. Khởi Tạo Dữ Liệu

Chạy lần lượt các lệnh sau:

```bash
# Tạo bảng User & Admin
python init_db.py

# Đăng ký thiết bị cảm biến
python seed_sensors.py

# Nạp dữ liệu bản đồ
python seed_data.py
```

---

## Chạy Ứng Dụng

Mở 2 terminal riêng biệt:

### Terminal 1: API Backend
```bash
python main.py
```
- **Server URL:** http://127.0.0.1:8000
- **API Documentation:** http://127.0.0.1:8000/docs

### Terminal 2: AQI Agent (Cập Nhật Dữ Liệu Realtime)
```bash
python aqi_agent.py
```

---

## API Endpoints

### Authentication & Users
```
POST   /api/auth/login           - Đăng nhập
POST   /api/auth/register        - Đăng ký
GET    /api/users/me             - Lấy thông tin user hiện tại
PUT    /api/users/{user_id}      - Cập nhật thông tin user
```

### Reports
```
GET    /api/reports              - Danh sách báo cáo
POST   /api/reports              - Gửi báo cáo sự cố
GET    /api/reports/{id}         - Chi tiết báo cáo
PUT    /api/reports/{id}         - Cập nhật báo cáo
DELETE /api/reports/{id}         - Xóa báo cáo
```

### Locations
```
GET    /api/locations            - Danh sách địa điểm
POST   /api/locations            - Tạo địa điểm mới
GET    /api/locations/{id}       - Chi tiết địa điểm
PUT    /api/locations/{id}       - Cập nhật địa điểm
DELETE /api/locations/{id}       - Xóa địa điểm
```

### News
```
GET    /api/news/hanoimoi        - Tin tức Hà Nội Mới
GET    /api/news/hanoimoi?limit=20
```

### Context Broker (Orion-LD)
```
GET    /ngsi-ld/v1/entities              - Lấy tất cả thực thể
GET    /ngsi-ld/v1/entities/{id}         - Chi tiết thực thể
POST   /ngsi-ld/v1/entities              - Tạo thực thể
PATCH  /ngsi-ld/v1/entities/{id}/attrs   - Cập nhật attributes
```

**Ví dụ truy vấn Orion-LD:**
```
GET http://localhost:1026/ngsi-ld/v1/entities?type=AirQualityObserved&limit=100
GET http://localhost:1026/ngsi-ld/v1/entities?type=PUBLIC_PARK&limit=100
```

**Headers bắt buộc cho Orion-LD:**
```http
Accept: application/ld+json
Link: <https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"
```

---

## Cấu Trúc Thư Mục

```
├── app/
│   ├── api/              # API routes
│   ├── crud/             # Database operations
│   ├── db/               # Database session
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── workers/          # Background tasks
├── Data/                 # GeoJSON files
├── main.py               # FastAPI entry point
├── aqi_agent.py          # AQI update service
├── init_db.py            # Database initialization
├── seed_data.py          # Sample data
├── seed_sensors.py       # Sensor registration
├── docker-compose.yml    # Docker services
└── requirements.txt      # Python dependencies
```

---

## Xử Lý Sự Cố

### Lỗi kết nối Database
```bash
docker-compose down
docker-compose up -d
```

### Lỗi WinError 121 / Socket hang up
```bash
# Khởi động lại server
Ctrl+C
python main.py
```

### API trả về danh sách rỗng
- Kiểm tra xem đã chạy `seed_data.py` chưa
- Kiểm tra Headers `Link` khi gọi Orion-LD đã đúng chưa

### Xem logs Docker
```bash
docker-compose logs -f service_name
```

---

## Contributors

Dự án này được phát triển bởi HouHackathon-CQP.
