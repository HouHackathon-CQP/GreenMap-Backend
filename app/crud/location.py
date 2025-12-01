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

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GreenLocation, LocationType
from app.schemas import LocationCreate


async def create_location(db: AsyncSession, location: LocationCreate) -> GreenLocation:
    wkt_location = f"SRID=4326;POINT({location.longitude} {location.latitude})"
    db_location = GreenLocation(
        name=location.name,
        location_type=location.location_type,
        description=location.description,
        location=wkt_location,
    )
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


async def get_locations(
    db: AsyncSession,
    location_type: Optional[LocationType] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(GreenLocation)
    if location_type:
        query = query.where(GreenLocation.location_type == location_type)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
