from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(alias="username")
    password: str

    model_config = ConfigDict(populate_by_name=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
