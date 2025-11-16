from pydantic import BaseModel, ConfigDict, computed_field, Field 
from typing import Any
from models import LocationType
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
    """Khuôn cơ bản, chứa các trường chung."""
    email: str
    full_name: str | None = None


class UserCreate(UserBase):
    """
    Khuôn TẠO MỚI (Đăng ký).
    Frontend sẽ gửi lên 'password' (mật khẩu chay).
    """
    password: str
    
    # Ví dụ JSON Frontend gửi lên:
    # {
    #   "email": "user@example.com",
    #   "full_name": "Test User",
    #   "password": "this_is_a_secret"
    # }


class UserRead(UserBase):
    """
    Khuôn ĐỌC DỮ LIỆU (API trả về).
    TUYỆT ĐỐI KHÔNG trả về 'hashed_password'.
    """
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)