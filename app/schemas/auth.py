from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import UserRole

class LoginRequest(BaseModel):
    email: str = Field(alias="username")
    password: str

    model_config = ConfigDict(populate_by_name=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id: int
    email: str
    full_name: str | None = None
    role: UserRole
