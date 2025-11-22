from datetime import datetime, timezone

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, Text

from app.db.session import Base
from app.models.enums import ReportStatus


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
