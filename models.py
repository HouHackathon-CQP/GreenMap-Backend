import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Enum
from geoalchemy2 import Geometry 
from database import Base

# Dùng Enum để định nghĩa các loại địa điểm một cách "sạch sẽ"
class LocationType(str, enum.Enum):
    CHARGING_STATION = "CHARGING_STATION" # Trạm sạc xanh
    GREEN_SPACE = "GREEN_SPACE"         # Điểm nghỉ xanh [cite: 2611-3403]
    PUBLIC_PARK = "PUBLIC_PARK"         # Công viên [cite: 2611-3403]
    BICYCLE_RENTAL = "BICYCLE_RENTAL"   # Điểm thuê xe đạp [cite: 3404-3610]
    TOURIST_ATTRACTION = "TOURIST_ATTRACTION" # Địa điểm du lịch [cite: 1-1985]
    # Sau này có thể thêm: SENSOR_STATION (Trạm đo), ...

class GreenLocation(Base):
    """
    Bản thiết kế cho bảng "green_locations" trong CSDL.
    """
    __tablename__ = "green_locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Dùng Enum để đảm bảo dữ liệu luôn đúng 1 trong các loại trên
    location_type = Column(Enum(LocationType), nullable=False, index=True)

    # Cột Lưu tọa độ (Kinh độ, Vĩ độ)
    # 'POINT' là kiểu hình học
    # 'srid=4326' là hệ tọa độ chuẩn (WGS 84) mà GPS hay dùng.
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    description = Column(Text, nullable=True)
    data_source = Column(String(100), default="admin_added") 
    
    external_id = Column(String(255), nullable=True, index=True) # ID từ OpenStreetMap
    is_active = Column(Boolean, default=True) # Dùng để cho Admin duyệt

class User(Base):
    """
    Bản thiết kế cho bảng "users".
    Cần cho các tính năng:
    - Cộng đồng xanh (báo cáo ô nhiễm) 
    - Gamification (tích điểm) 
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Email dùng để đăng nhập, phải là duy nhất
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    full_name = Column(String(255), nullable=True) # Tên đầy đủ (tùy chọn)

    # Cột quan trọng: KHÔNG LƯU MẬT KHẨU
    # Chỉ lưu "mật khẩu đã băm"
    hashed_password = Column(String(255), nullable=False)
    
    # Dùng để "khóa" tài khoản nếu cần
    is_active = Column(Boolean, default=True)

    # (Sau này có thể thêm 'is_superuser' cho Admin)