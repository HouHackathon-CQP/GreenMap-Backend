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

from typing import Any, Optional

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import LocationType


class LocationBase(BaseModel):
    name: str
    location_type: LocationType
    description: str | None = None


class LocationCreate(LocationBase):
    latitude: float
    longitude: float

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_type: Optional[LocationType] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None

class LocationRead(LocationBase):
    id: int
    data_source: str | None = None
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
