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
SECRET_KEY="your_secret_key_here_64_chars"
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

# Firebase push notification
FIREBASE_CREDENTIALS_FILE="/path/to/firebase-service-account.json"
FIREBASE_DEFAULT_TOPIC="greenmap-daily"

# Daily notification schedule (local server time)
DAILY_PUSH_HOUR=7
DAILY_PUSH_MINUTE=0
DAILY_PUSH_TITLE="Bản đồ Xanh - Cập nhật môi trường mỗi ngày"
DAILY_PUSH_BODY="Mở ứng dụng để xem dự báo thời tiết và chất lượng không khí hôm nay."
```

### 5. Khởi Động Docker
```bash
docker-compose up -d
```
⏳ Chờ 10-15 giây để các container khởi động hoàn toàn.

### 6. Khởi Tạo Dữ Liệu

Chạy lệnh sau:
```bash
# Tự động chạy các lệnh khởi tạo dữ liệu 
python setup_project.py
```

Hoặc chạy lần lượt các lệnh sau (dễ debug hơn):

```bash
# Nối file dữ liệu JSON
python Data/merge_json.py

# Tạo tất cả bảng database (users, locations, reports, notification_tokens, notification_history, v.v.)
python init_db.py

# Đăng ký thiết bị cảm biến
python seed_sensor.py

# Nạp dữ liệu bản đồ
python import_osm.py 
python sync_to_orion.py

# Xử lý dữ liệu giao thông mô phỏng 
python process_simulation.py
```

> **Lưu ý**: `init_db.py` tự động tạo tất cả các bảng được định nghĩa trong models, bao gồm cả bảng `notification_history` cho tính năng lịch sử thông báo.


---

## Chạy Ứng Dụng

Mở 4 terminal riêng biệt:

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

### Terminal 4: Daily Notification Job (gửi push Firebase hằng ngày)
```bash
python notification_job.py
```
> Yêu cầu cấu hình `FIREBASE_CREDENTIALS_FILE` và đồng bộ device token từ mobile app.

---

## API Endpoints

### System
```
GET    /                         - Root endpoint
GET    /test-db                  - Test database connection
```

### Authentication
```
POST   /login                    - Đăng nhập (trả về access_token)
POST   /logout                   - Đăng xuất (yêu cầu xác thực)
```

### Users
```
GET    /users                    - Lấy danh sách user (yêu cầu xác thực)
POST   /users                    - Đăng ký user mới (không cần xác thực)
GET    /users/{user_id}          - Lấy thông tin user theo ID (yêu cầu xác thực)
PUT    /users/{user_id}          - Cập nhật thông tin user (Admin hoặc chính user đó)
DELETE /users/{user_id}          - Xóa user (chỉ Admin)
POST   /users/change-password/me - Đổi mật khẩu user hiện tại (yêu cầu xác thực)
```

### Locations
```
GET    /locations                - Lấy danh sách địa điểm từ Orion-LD
POST   /locations                - Tạo địa điểm mới (yêu cầu xác thực)
GET    /locations/{location_id}  - Lấy chi tiết địa điểm từ Postgres (để Admin sửa)
PUT    /locations/{location_id}  - Cập nhật địa điểm -> Đồng bộ sang Orion (yêu cầu xác thực)
DELETE /locations/{location_id}  - Xóa địa điểm -> Xóa khỏi Orion (yêu cầu xác thực)
```

**Location Types:** `CHARGING_STATION`, `GREEN_SPACE`, `PUBLIC_PARK`, `BICYCLE_RENTAL`, `TOURIST_ATTRACTION`

### Reports
```
GET    /reports                  - Lấy danh sách báo cáo (yêu cầu xác thực)
POST   /reports                  - Tạo báo cáo sự cố mới (yêu cầu xác thực)
PUT    /reports/{report_id}/status - Cập nhật trạng thái báo cáo (yêu cầu xác thực)
```

**Report Status:** `PENDING`, `APPROVED`, `REJECTED`

### News
```
GET    /news/hanoimoi            - Lấy tin tức từ Hà Nội Mới
```

### Air Quality Index (AQI)
```
GET    /aqi/hanoi                - Lấy dữ liệu AQI từ Orion-LD
                                  - Hỗ trợ: ?limit=100 (max 1000 do đặc thù của Orion_LD)
```

### Weather
```
GET    /weather/hanoi            - Lấy dữ liệu thời tiết các quận từ Orion-LD
GET    /weather/forecast         - Dự báo thời tiết chi tiết (Trực tiếp từ Open-Meteo)
                                  - Hỗ trợ: ?lat=21.0285&lon=105.8542
                                  - Trả về: Hiện tại, 24h tới, 7 ngày tới
```

### Traffic
```
GET    /traffic/segments         - Lấy bản đồ nền (GeoJSON) các đoạn đường giao thông
GET    /traffic/live             - Lấy trạng thái giao thông hiện tại
```

### AI Insights (Gemini / Groq)
```
POST   /ai/weather-insights      - Phân tích thời tiết 24h/7 ngày + AQI bằng AI
                                  - Hỗ trợ: ?lat=21.0285&lon=105.8542&provider=auto&model=
                                  - Provider: gemini, groq, hoặc auto
```
> Cần cấu hình `GEMINI_API_KEY` hoặc `GROQ_API_KEY` trong `.env`.

### File Upload
```
POST   /upload                   - Upload image (multipart/form-data)
```

### Notifications (Firebase)
```
POST   /api/notifications/register              - Mobile đăng ký/ cập nhật device token
DELETE /api/notifications/register/{token}      - Hủy đăng ký token
GET    /api/notifications/tokens                - Danh sách token (Admin)
POST   /api/notifications/send                  - Gửi push broadcast (Admin)
POST   /api/notifications/send/topic            - Gửi push theo topic (Admin)
GET    /api/notifications/history               - Xem lịch sử thông báo (Admin)
GET    /api/notifications/history/{id}          - Chi tiết lịch sử (Admin)
DELETE /api/notifications/history/cleanup       - Dọn dẹp lịch sử cũ (Admin)
```

**Notification History**: Hệ thống tự động lưu lịch sử tất cả thông báo đã gửi, bao gồm số lượng thành công/thất bại, người gửi, thời gian, v.v. Hữu ích cho việc theo dõi và audit.

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
│   │       ├── notifications.py      # Notification & history endpoints
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
│   │   ├── notification.py           # Notification CRUD operations
│   │   ├── report.py                 # Report CRUD operations
│   │   └── user.py                   # User CRUD operations
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py                # Database session management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py                  # Enum definitions
│   │   ├── location.py               # Location model
│   │   ├── notification.py           # Notification & history models
│   │   ├── report.py                 # Report model
│   │   ├── traffic.py                # Traffic model
│   │   └── user.py                   # User model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py                   # Authentication schemas
│   │   ├── location.py               # Location schemas
│   │   ├── news.py                   # News schemas
│   │   ├── notification.py           # Notification schemas
│   │   ├── report.py                 # Report schemas
│   │   └── user.py                   # User schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openaq.py                 # OpenAQ API service
│   │   ├── orion.py                  # Orion-LD broker service
│   │   ├── push.py                   # Firebase push notification service
│   │   ├── rss.py                    # RSS feed service
│   │   └── weather.py                # Weather API service
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── aqi_agent.py              # AQI data update worker
│   │   ├── notification_job.py       # Daily push notification worker
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
├── notification_job.py               # Daily push notification scheduler
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

## Changelog

Xem [CHANGELOG.md](CHANGELOG.md) để biết lịch sử thay đổi chi tiết của dự án.

---

## Contributors

Dự án này được phát triển bởi HouHackathon-CQP.

## Đóng góp

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết chi tiết về:
- Quy trình gửi Pull Request
- Hướng dẫn commit message
- Quy tắc code và cộng đồng

## Liên hệ

- Repository: [https://github.com/HouHackathon-CQP/GreenMap-Backend](https://github.com/HouHackathon-CQP/GreenMap-Backend)
- Issues: [https://github.com/HouHackathon-CQP/GreenMap-Backend/issues](https://github.com/HouHackathon-CQP/GreenMap-Backend/issues)