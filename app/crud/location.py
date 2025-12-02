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
from app.schemas import LocationCreate, LocationUpdate
from geoalchemy2.elements import WKTElement


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

async def get_location(db: AsyncSession, location_id: int) -> GreenLocation | None:
    result = await db.execute(select(GreenLocation).where(GreenLocation.id == location_id))
    return result.scalar_one_or_none()

async def update_location(db: AsyncSession, db_obj: GreenLocation, obj_in: LocationUpdate) -> GreenLocation:
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # Xử lý tọa độ nếu có thay đổi
    if "latitude" in update_data and "longitude" in update_data:
        lat = update_data.pop("latitude")
        lon = update_data.pop("longitude")
        update_data["location"] = WKTElement(f"POINT({lon} {lat})", srid=4326)
    elif "latitude" in update_data: update_data.pop("latitude")
    elif "longitude" in update_data: update_data.pop("longitude")

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def delete_location(db: AsyncSession, location_id: int):
    location = await get_location(db, location_id)
    if location:
        await db.delete(location)
        await db.commit()
    return location
