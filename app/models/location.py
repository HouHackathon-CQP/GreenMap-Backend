# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
