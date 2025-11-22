from pydantic import BaseModel, ConfigDict

from app.models.enums import ReportStatus


class ReportBase(BaseModel):
    title: str
    description: str | None = None
    latitude: float
    longitude: float
    image_url: str | None = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    status: ReportStatus


class ReportRead(ReportBase):
    id: int
    user_id: int
    status: ReportStatus
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
