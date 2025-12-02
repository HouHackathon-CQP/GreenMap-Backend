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

# NGSI-LD config (Context & Type)
NGSI_CONTEXT_URL=https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld
NGSI_TYPE_AQI=https://smartdatamodels.org/dataModel.Environment/AirQualityObserved
NGSI_TYPE_WEATHER=https://smartdatamodels.org/dataModel.Environment/WeatherObserved
```

### 5. Khởi Động Docker
```bash
docker-compose up -d
```
⏳ Chờ 10-15 giây để các container khởi động hoàn toàn.

### 6. Khởi Tạo Dữ Liệu

Chạy lần lượt các lệnh sau:

```bash
# Nối file dữ liệu JSON
python Data/merge_json.py

# Tạo bảng User & Admin
python init_db.py

# Đăng ký thiết bị cảm biến
python seed_sensor.py

# Nạp dữ liệu bản đồ
python import_osm.py 
python sync_to_orion.py

# Xử lý dữ liệu giao thông mô phỏng 
python process_simulation.py
```

---

## Chạy Ứng Dụng

Mở 3 terminal riêng biệt:

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

### Terminal 3: Weather Agent (Cập Nhật Dữ Liệu Realtime)
```bash
python weather_agent.py
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
GreenMap-Backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api.py                    # API router configuration
│   │   ├── deps.py                   # Dependency injection
│   │   └── routes/
│   │       ├── aqi.py                # Air Quality Index endpoints
│   │       ├── auth.py               # Authentication endpoints
│   │       ├── locations.py          # Location management endpoints
│   │       ├── news.py               # News endpoints
│   │       ├── reports.py            # Report management endpoints
│   │       ├── system.py             # System endpoints
│   │       ├── traffic.py            # Traffic data endpoints
│   │       ├── uploads.py            # File upload endpoints
│   │       ├── users.py              # User management endpoints
│   │       └── weather.py            # Weather endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration settings
│   │   └── security.py               # Security utilities
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── location.py               # Location CRUD operations
│   │   ├── report.py                 # Report CRUD operations
│   │   └── user.py                   # User CRUD operations
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py                # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py                  # Enum definitions
│   │   ├── location.py               # Location model
│   │   ├── report.py                 # Report model
│   │   ├── traffic.py                # Traffic model
│   │   └── user.py                   # User model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Authentication schemas
│   │   ├── location.py               # Location schemas
│   │   ├── news.py                   # News schemas
│   │   ├── report.py                 # Report schemas
│   │   └── user.py                   # User schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openaq.py                 # OpenAQ API service
│   │   ├── orion.py                  # Orion-LD broker service
│   │   ├── rss.py                    # RSS feed service
│   │   └── weather.py                # Weather API service
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── aqi_agent.py              # AQI data update worker
│   │   └── weather_agent.py          # Weather data update worker
│   ├── __init__.py
│   └── main.py                       # FastAPI app initialization
├── Data/
│   ├── bicycle_rental.geojson        # Bicycle rental stations data
│   ├── charging_station.geojson      # EV charging stations data
│   ├── park.geojson                  # Parks data
│   ├── tourist_attractions.geojson   # Tourist attractions data
│   ├── simulation_data_part1.json    # Simulation data (part 1)
│   ├── simulation_data_part2.json    # Simulation data (part 2)
│   ├── merge_json.py                 # Script to merge JSON files
│   └── split_json.py                 # Script to split JSON files
├── static/
│   └── images/                       # Static image resources
├── main.py                           # FastAPI server entry point
├── aqi_agent.py                      # Standalone AQI update service
├── weather_agent.py                  # Standalone Weather update service
├── init_db.py                        # Database initialization script
├── seed_sensor.py                    # Sensor data seeding script
├── process_simulation.py             # Traffic simulation data processor
├── sync_to_orion.py                  # Sync data to Orion-LD broker
├── import_osm.py                     # OSM data import script
├── docker-compose.yml                # Docker Compose configuration
├── Dockerfile                        # Docker image build file
├── requirements.txt                  # Python dependencies
├── env.example                       # Example environment variables
├── README.md                         # Readme file
└── LICENSE                           # License file
```

### Mô Tả Chi Tiết:

- **app/** - Thư mục chứa ứng dụng FastAPI chính
  - **api/** - Định nghĩa API routes và endpoints
  - **core/** - Cấu hình và các tiện ích bảo mật
  - **crud/** - Các hàm để tương tác với database
  - **db/** - Quản lý kết nối database
  - **models/** - Định nghĩa model SQLAlchemy
  - **schemas/** - Pydantic schemas cho validation
  - **services/** - Logic nghiệp vụ tích hợp API ngoài
  - **workers/** - Background tasks và agent workers

- **Data/** - Dữ liệu GeoJSON và simulation data

- **Root Scripts** - Các script standalone cho initialization và maintenance

- **Docker** - Cấu hình Docker cho containerization

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
- Kiểm tra xem đã chạy `import_osm.py` và `sync_to_orion.py` chưa
- Kiểm tra Headers `Link` khi gọi Orion-LD đã đúng chưa

### Xem logs Docker
```bash
docker-compose logs -f service_name
```

---

## Contributors

Dự án này được phát triển bởi HouHackathon-CQP.
