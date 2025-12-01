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

from typing import List, Optional, Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.core.config import settings
from app.models.enums import LocationType

router = APIRouter(prefix="/locations", tags=["locations"])

ORION_UPSERT_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entityOperations/upsert?options=update"
ORION_ENTITIES_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
CONTEXT = "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld"

HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/json"
}

async def push_location_to_orion(location: schemas.LocationCreate, location_id: int):
    """
    Chuyển đổi LocationCreate thành NGSI-LD Entity và gửi sang Orion.
    Sử dụng cơ chế UPSERT (Update/Insert) để tránh lỗi 409 Conflict.
    """
    entity_id = f"urn:ngsi-ld:{location.location_type}:{location_id}"
    payload = {
        "id": entity_id,
        "type": location.location_type, 
        
        "name": {
            "type": "Property",
            "value": location.name
        },
        
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [location.longitude, location.latitude]
            }
        },
        
        "source": {
            "type": "Property",
            "value": "Admin Created"
        },
        
        "@context": CONTEXT
    }

    if location.description:
        payload["description"] = {
            "type": "Property",
            "value": location.description
        }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                ORION_UPSERT_URL, 
                json=[payload],
                headers=HEADERS,
                timeout=10.0
            )

            if response.status_code in [201, 204]:
                print(f"✅ Đã đồng bộ địa điểm {entity_id} sang Orion-LD.")
            else:
                print(f"❌ Lỗi Orion-LD ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"❌ Lỗi kết nối Orion-LD: {e}")


@router.post("", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    """
    Tạo địa điểm mới:
    1. Lưu vào PostgreSQL (để lấy ID và quản lý nghiệp vụ).
    2. Đẩy sang Orion-LD (để hiển thị bản đồ và Linked Data).
    """
    db_location = await crud.create_location(db=db, location=location)
    await push_location_to_orion(location, db_location.id)

    return db_location


@router.get("")
async def read_all_locations(
    location_type: Optional[LocationType] = None,
    offset: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua (Offset)"),
    limit: int = Query(100, ge=1, le=1000, description="Số lượng bản ghi tối đa"),
    options: str = "keyValues", 
) -> List[Dict[str, Any]]: 
    """
    Lấy danh sách địa điểm từ Orion-LD (Hỗ trợ phân trang skip/limit).
    """
    
    params = {
        "limit": limit,
        "offset": offset,
        "options": options 
    }

    if location_type:
        params["type"] = location_type.value

    read_headers = {
        "Accept": "application/ld+json",
        "Link": f'<{CONTEXT}>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ORION_ENTITIES_URL, params=params, headers=read_headers)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=f"Orion Error: {exc.response.text}")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exc)}")