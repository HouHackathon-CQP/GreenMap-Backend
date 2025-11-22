from sqlalchemy import Boolean, Column, Enum, Integer, String, Text
from geoalchemy2 import Geometry

from app.db.session import Base
from app.models.enums import LocationType


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
