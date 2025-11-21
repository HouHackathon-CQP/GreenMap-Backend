from pydantic import BaseModel, ConfigDict, computed_field, Field 
from typing import Any
from models import LocationType, UserRole, ReportStatus
from geoalchemy2.shape import to_shape

class LocationBase(BaseModel):
    name: str
    location_type: LocationType
    description: str | None = None

class LocationCreate(LocationBase):
    latitude: float
    longitude: float

class LocationRead(LocationBase):
    id: int
    data_source: str
    is_active: bool

    location: Any = Field(exclude=True) 

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def latitude(self) -> float:
        if self.location:
            shape = to_shape(self.location)
            return shape.y
        return 0.0

    @computed_field
    @property
    def longitude(self) -> float:
        if self.location:
            shape = to_shape(self.location)
            return shape.x
        return 0.0
    

# User Schemas 
class UserBase(BaseModel):
    email: str
    full_name: str | None = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    role: UserRole 
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS CHO BÁO CÁO ---

class ReportBase(BaseModel):
    title: str
    description: str | None = None
    latitude: float
    longitude: float
    image_url: str | None = None

# Khuôn để người dân GỬI báo cáo
class ReportCreate(ReportBase):
    pass

# Khuôn để Admin CẬP NHẬT trạng thái
class ReportUpdate(BaseModel):
    status: ReportStatus

# Khuôn để TRẢ VỀ dữ liệu (cho Admin/App xem)
class ReportRead(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)