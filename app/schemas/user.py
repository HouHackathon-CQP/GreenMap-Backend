from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


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
