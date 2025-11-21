import enum
from datetime import datetime, timezone 
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Text, Float
from geoalchemy2 import Geometry
from database import Base

# --- 1. CÁC ENUM (Định nghĩa loại) ---

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CITIZEN = "CITIZEN"

class LocationType(str, enum.Enum):
    CHARGING_STATION = "CHARGING_STATION"
    GREEN_SPACE = "GREEN_SPACE"
    PUBLIC_PARK = "PUBLIC_PARK"
    BICYCLE_RENTAL = "BICYCLE_RENTAL"
    TOURIST_ATTRACTION = "TOURIST_ATTRACTION"

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# --- 2. CÁC BẢNG (MODELS) ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN, nullable=False)

class GreenLocation(Base):
    __tablename__ = "green_locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    location_type = Column(Enum(LocationType), nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    is_active = Column(Boolean, default=True)
    data_source = Column(String(100), nullable=True) 
    external_id = Column(String(100), nullable=True) 

class UserReport(Base):
    __tablename__ = "user_reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(String(50), default=lambda: datetime.now(timezone.utc).isoformat())